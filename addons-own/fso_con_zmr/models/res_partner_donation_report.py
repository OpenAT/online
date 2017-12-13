# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.fso_base.tools.datetime import naive_to_timezone

import datetime
import pytz

import logging
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


# Austrian Finanzamt Donation Reports (Spendenberichte pro Person fuer ein Jarh)
# HINT: FA Donation Report = Spendenreport fuer das Finanzamt Oesterreich
class ResPartnerFADonationReport(models.Model):
    _name = 'res.partner.donation_report'
    _order = 'anlage_am_um DESC'

    # ------
    # FIELDS
    # ------
    # HINT: 'fields' can only be set in FS-Online in state 'new'
    # HINT: 'transmission' means 'Uebertragung lauft' oder wird vorbereited
    # ATTENTION: All donation reports from FRST MUST have the state 'prepared' to avoid any editing in FS-Online !
    state = fields.Selection(string="State", readonly=True, default='new',
                             selection=[('new', 'New'),
                                        ('prepared', 'Prepared for Submission'),
                                        ('submitted', 'Submitted'),
                                        ('skipped', 'Skipped'),
                                        ('error', 'Error')])

    # Submission data (Values from Fundraising Studio if submission_env is p)
    # -----------------------------------------------------------------------
    # ATTENTION: This will determine the submission url!
    submission_env = fields.Selection(string="Environment", selection=[('t', 'Test'), ('p', 'Production')],
                                      required=True)

    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner',  required=True)
    bpk_company_id = fields.Many2one(string="BPK Company", comodel_name='res.company',  required=True)

    anlage_am_um = fields.Datetime(string="Donation Report Create Date", required=True, default=fields.datetime.now(),
                                   help=_("This is used for the order of the submission_type computation!"))
    ze_datum_von = fields.Datetime(string="Donation Report Start", required=True)
    ze_datum_bis = fields.Datetime(string="Donation Report End", required=True)

    mj_range = [(str(i), str(i)) for i in range(2017, int(datetime.datetime.now().year)+11)]
    meldungs_jahr = fields.Selection(string="Donation Report Year (Zeitraum)", required=True, selection=mj_range)
    betrag = fields.Float(string="Donation Report Total (Betrag)", required=True)

    # Fields computed (or set) just before transmission
    # -------------------------------------------------
    submission_id = fields.Many2one(string="Submission",
                                    help="submission_id.id is used as the MessageRefId !",
                                    comodel_name="res.partner.donation_report.submission", readonly=True)
    submission_state = fields.Selection(related="submission_id.state")
    submission_datetime = fields.Datetime(related="submission_id.submission_datetime")
    submission_url = fields.Char(related="submission_id.submission_url")
    submission_fa_dr_type = fields.Char(related="submission_id.submission_fa_dr_type")

    submission_type = fields.Selection(string="Donation Report Type", readonly=True,
                                       selection=[('E', 'Erstuebermittlung'),
                                                  ('A', 'Aenderungsuebermittlung'),
                                                  ('S', 'Stornouebermittlung')])

    # ATTENTION: Follow-Up Reports of type A or S will share the same number
    # Format: D(for Dadi)-[meldungs_jahr]-[fa_dr_type]-[partner_id.id]
    submission_refnr = fields.Char(string="Reference Number (RefNr)", readonly=True, size=23,
                                   help="Die RefNr muss pro Uebermittler, Jahr und "
                                        "Uebermittlungsart eindeutig sein. (z.B.: D-2017-KK-34791")

    # HINT: If set the BPK forced field values are copied
    submission_firstname = fields.Char(string="Firstname", readonly=True)
    submission_lastname = fields.Char(string="Lastname", readonly=True)
    submission_birthdate_web = fields.Date(string="Lastname", readonly=True)
    submission_zip = fields.Char(string="ZIP Code", readonly=True)
    submission_bpk_public = fields.Char(string="Public BPK (vbPK)", readonly=True)

    response_content = fields.Text(string="Response", readonly=True)

    # Error
    # -----
    error = fields.Selection(string="Error", readonly=True,
                             selection=[('submission_error', 'Submission Error'),
                                        ('response_error', 'Response Error'),
                                        ('bpk_pending', 'BPK-Request pending'),
                                        ('bpk_missing', 'BPK Missing')])
    error_code = fields.Char(string="Error Code", redonly=True)
    error_detail = fields.Text(string="Error Detail", readonly=True)

    # Related Donation Reports
    # ------------------------
    report_erstmeldung_id = fields.Many2one(string="Zugehoerige Erstmeldung", comodel_name='res.partner.donation_report',
                                            readonly=True)
    report_follow_up_ids = fields.One2many(string="Follow-Up Reports", comodel_name="res.partner.donation_report",
                                           inverse_name="report_erstmeldung_id", readonly=True)

    # Skipped Info
    # ------------
    skipped_by_id = fields.Many2one(string="Skipped by Report", comodel_name='res.partner.donation_report',
                                    readonly=True)
    skipped = fields.One2many(string="Skipped the Reports", comodel_name="res.partner.donation_report",
                              inverse_name="skipped_by_id", readonly=True)

    @api.constrains('meldungs_jahr', 'betrag', 'ze_datum_von', 'ze_datum_bis')
    def _check_field_constrains(self):
        now = datetime.datetime.now()
        min_year = 2017
        max_year = int(now.year)+1
        for r in self:

            # Check year (meldungs_jahr)
            if not r.meldungs_jahr or int(r.meldungs_jahr) < min_year or int(r.meldungs_jahr) > max_year:
                raise ValidationError(_("Year must be inside %s - %s") % (min_year, max_year))

            # Check total (betrag)
            if r.betrag < 0:
                raise ValidationError(_("Total can not be negative!"))

            # Check donation report range (ze_datum_von, ze_datum_bis)
            if r.ze_datum_von and r.ze_datum_bis:
                year_start = datetime.datetime(int(r.meldungs_jahr), 01, 01, 00, 00, 00)
                year_start -= datetime.timedelta(15)
                year_end = datetime.datetime(int(r.meldungs_jahr), 12, 31, 23, 59, 59, 999)
                year_end += datetime.timedelta(15)
                von = datetime.datetime.strptime(r.ze_datum_von, DEFAULT_SERVER_DATETIME_FORMAT)
                bis = datetime.datetime.strptime(r.ze_datum_bis, DEFAULT_SERVER_DATETIME_FORMAT)
                print r.ze_datum_von
                if von < year_start or bis > year_end:
                    raise ValidationError(_("Report range seems to be outside of the report year %s! "
                                            "Please check ze_datum_von and ze_datum_bis."
                                            "") % (r.ze_datum_von, r.ze_datum_bis, r.meldungs_jahr))

    @api.onchange('meldungs_jahr')
    def _oc_meldungs_jahr(self):
        vtz = pytz.timezone("Europe/Vienna")
        for r in self:
            if r.meldungs_jahr:
                if not r.ze_datum_von:
                    year_start = datetime.datetime(int(r.meldungs_jahr), 01, 01, 00, 00, 00)
                    year_start = naive_to_timezone(naive=year_start, naive_tz=vtz, naive_dst=True, target_tz=pytz.UTC)
                    r.ze_datum_von = year_start
                if not r.ze_datum_bis:
                    year_end = datetime.datetime(int(r.meldungs_jahr), 12, 31, 23, 59, 59, 999)
                    year_end = naive_to_timezone(naive=year_end, naive_tz=vtz, naive_dst=True, target_tz=pytz.UTC)
                    r.ze_datum_bis = year_end
