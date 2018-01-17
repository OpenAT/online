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

    now = fields.datetime.now

    # ------
    # FIELDS
    # ------
    # HINT: 'fields' can only be changed in FS-Online in state 'new'
    state = fields.Selection(string="State", readonly=True, default='new',
                             selection=[('new', 'New'),
                                        ('skipped', 'Skipped'),
                                        ('error', 'Error'),
                                        ('submitted', 'Submitted to FinanzOnline'),
                                        ('response_ok', 'Accepted by FinanzOnline'),
                                        ('response_nok', 'Rejected by FinanzOnline'),
                                        ('unexpected_response', 'Unexpected Response')])

    # Generic Field for extra Information like
    info = fields.Text(string="Info", readonly=True)

    # Donation report submission
    submission_id = fields.Many2one(string="Submission",
                                    help="submission_id.id is used as the MessageRefId !",
                                    comodel_name="res.partner.donation_report.submission",
                                    readonly=True, states={'new': [('readonly', False)]})

    # Related Fields from the donation report submission (drs)
    # TODO: related fields seem to be pretty slow - it may be better to just update them by the write or update method?
    submission_id_state = fields.Selection(related="submission_id.state", store=True, readonly=True)
    submission_id_datetime = fields.Datetime(related="submission_id.submission_datetime", store=True,  readonly=True)
    submission_id_url = fields.Char(related="submission_id.submission_url", store=True,  readonly=True)
    submission_id_fa_dr_type = fields.Char(related="submission_id.submission_fa_dr_type", store=True,  readonly=True)

    # Data for submission (normally from Fundraising Studio)
    # ------------------------------------------------------
    # ATTENTION: This will determine the submission url!
    submission_env = fields.Selection(string="Environment", selection=[('t', 'Test'), ('p', 'Production')],
                                      required=True, readonly=True, states={'new': [('readonly', False)]})
    # TODO: Create an inverse Field
    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner',  required=True,
                                 readonly=True, states={'new': [('readonly', False)]})
    # TODO: Create an inverse Field
    bpk_company_id = fields.Many2one(string="BPK Company", comodel_name='res.company',  required=True,
                                     readonly=True, states={'new': [('readonly', False)]})

    anlage_am_um = fields.Datetime(string="Donation Report Create Date", required=True, default=fields.datetime.now(),
                                   readonly=True, states={'new': [('readonly', False)]},
                                   help=_("This is used for the order of the submission_type computation!"))
    ze_datum_von = fields.Datetime(string="Donation Report Start", required=True,
                                   readonly=True, states={'new': [('readonly', False)]})
    ze_datum_bis = fields.Datetime(string="Donation Report End", required=True,
                                   readonly=True, states={'new': [('readonly', False)]})

    meldungs_jahr = fields.Selection(string="Donation Report Year (Zeitraum)", required=True,
                                     readonly=True, states={'new': [('readonly', False)]},
                                     selection=[(str(i), str(i)) for i in range(2017, int(now().year)+11)])
    betrag = fields.Float(string="Donation Report Total (Betrag)", required=True,
                          readonly=True, states={'new': [('readonly', False)]})

    # FORCE the public bpk:
    # HINT: This must be set by FRST when it creates a cancellation donation report for a partner where the bpk has
    #       changed or removed after a donation report was already submitted
    bpk_public_forced = fields.Char(string="Forced Public BPK (vbPK)", readonly=True)

    # BPK request
    # -----------
    # ATTENTION: These fields are all set or updated at create or write of the method or at any create, write and
    #            unlink of an bpk request (res.partner.bpk)
    # TODO: This should NOT be a computed field but set by bok methods create, write and unlink - this is the only
    #       reliable way!
    # TODO: Create an inverse field
    bpk_id = fields.Many2one(string="Partner/Company BPK", comodel_name='res.partner.bpk', readonly=True)
    bpk_state = fields.Selection(string="BPK State", readonly=True)
    bpk_public = fields.Char(string="BPK Public", readonly=True)
    bpk_private = fields.Char(string="BPK Private", readonly=True)



    # Fields computed (or recomputed) just before submission to FinanzOnline
    # ----------------------------------------------------------------------
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
    submission_bpk_private = fields.Char(string="Private BPK", readonly=True)

    # HINT: This field may not be available if the addon fs_sosync is not installed
    submission_sosync_fs_id = fields.Char(string="Fundraising Studio ID", readonly=True)

    # FinanzOnline XML Response
    # HINT: response_content will only hold the xml snippets related to this donation report based on submission_refnr
    response_content = fields.Text(string="Response Content", readonly=True)
    response_error_code = fields.Char(string="Response Error Code", readonly=True)
    response_error_detail = fields.Text(string="Response Error Detail", readonly=True)

    # Error
    # -----
    error_type = fields.Selection(string="Error Type", readonly=True,
                                  selection=[('bpk_missing', 'BPK Missing'),
                                             ('bpk_not_unique', 'BPK Not Unique'),     # multiple partners with same bpk
                                             ('data_incomplete', 'Data Incomplete'),   # should never happen!
                                             ('response_error', 'Error from FinanzOnline')])
    error_code = fields.Char(string="Error Code", redonly=True)
    error_detail = fields.Text(string="Error Detail", readonly=True)

    # Related Donation Reports
    # ------------------------
    # Erstmeldung
    report_erstmeldung_id = fields.Many2one(string="Zugehoerige Erstmeldung",
                                            comodel_name='res.partner.donation_report', readonly=True)
    # Follow Up reports to this Erstmeldung
    report_follow_up_ids = fields.One2many(string="Follow-Up Reports", comodel_name="res.partner.donation_report",
                                           inverse_name="report_erstmeldung_id", readonly=True)
    # Skipped by donation report
    skipped_by_id = fields.Many2one(string="Skipped by Report", comodel_name='res.partner.donation_report',
                                    readonly=True)
    # This report skipped these donation reports
    skipped = fields.One2many(string="Skipped the Reports", comodel_name="res.partner.donation_report",
                              inverse_name="skipped_by_id", readonly=True)

    # ---------------
    # COMPUTED FIELDS
    # ---------------

    # -------------
    # FIELD METHODS (compute, onchange, constrains)
    # -------------
    # TODO: check if api.constrains also fires on xmlrpc calls
    @api.constrains('meldungs_jahr', 'betrag', 'ze_datum_von', 'ze_datum_bis')
    def _check_submission_data_constrains(self):
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

    # TODO: check if api.constrains also fires on xmlrpc calls
    @api.constrains('submission_id', 'bpk_public')
    def _check_donation_report_submission_link(self):
        for r in self:

            # Unlink from donation report submission if the bpk was not found
            # TODO: Check if write works here?!?
            if not r.bpk_public and r.submission_id and r.state in ('new',):
                r.write({'submission_id': False})

            if r.submission_id:
                if r.state not in ('new',):
                    raise ValidationError(_("You can not change the donation report submission in state %s!") % r.state)
                if not r.bpk_public:
                    raise ValidationError(_("You can not link to a donation report submission without a public BPK!"))
            if not r.submission_id and r.state not in ('new',):
                raise ValidationError(_("You can not unlink from the donation report submission in state %s!"
                                        "") % r.state)

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

    def _check_mandatory_fields(self, values={}):
        _mandatory_fields = ('submission_env', 'partner_id', 'bpk_company_id', 'anlage_am_um', 'ze_datum_von',
                             'ze_datum_bis', 'meldungs_jahr', 'betrag')
        return (field for field in _mandatory_fields if not values.get(field))

    @api.multi
    def _same_bpk_different_partner(self):
        """
        This will find all donation reports with the same bpk_private but with a different partner (duplicates)
        :return: recordset
        """
        assert self.ensure_one(), _("_same_bpk_different_partner() works only for one record!")
        if not self.bpk_private:
            return self.env['res.partner.donation_report']
        # Find donation reports with the same bpk and company but with a different partner
        duplicates = self.sudo().search([('bpk_private', '=', self.bpk_private),
                                         ('bpk_request_company_id', '=', self.bpk_company_id),
                                         ('bpk_request_partner_id', '!=', self.partner_id)])
        return duplicates

    # TODO: run the 'write' method of donation reports also when the bpk method 'create' or 'write' is called so that
    #       BPK updates will update donation reports also!
    @api.multi
    def compute_bpk_fields(self):
        for report in self:
            # FIND the related bpk(s)
            bpk = self.env['res.partner.bpk']

            # Search for a bpk request with this partner and company
            if report.partner_id and report.bpk_company_id:
                bpk = bpk.sudo().search([('bpk_request_partner_id', '=', report.partner_id),
                                         ('bpk_request_company_id', '=', report.bpk_company_id)])

            # Update the bpk_id fields
            if not bpk:
                report.write({'bpk_id': False, 'bpk_state': False, 'bpk_public': False, 'bpk_private': False})
            elif len(bpk) == 1:
                report.write({'bpk_id': bpk.id, 'bpk_state': bpk.state,
                              'bpk_public': bpk.bpk_public, 'bpk_private': bpk.bpk_private})
            elif len(bpk) > 1:
                report.write({'bpk_id': False, 'bpk_state': False, 'bpk_public': False, 'bpk_private': False})
                raise ValidationError(_("More than one BPK found for partner %s (ID %s) and company %s (ID %s)!")
                                      % (report.partner_id.name, report.partner_id.id,
                                         report.bpk_company_id.name, report.bpk_company_id.id))

    @api.model
    def create(self, vals):
        # CHECK mandatory fields
        missing_fields = self._check_mandatory_fields(values=vals)
        if missing_fields:
            raise ValidationError(_("Mandatory donation report field(s) %s missing!") % str(missing_fields))

        # Create the donation report in the current environment (memory only right now)
        # ATTENTION: 'self' is still empty but the record 'exits' in the 'res' recordset already so every change
        #            or method call must be done to res and not to self
        # Other stuff done ba the in memory creation
        #     - Values validation (through API constrains above)
        #     - bpk_id computed (and other computed fields)
        res = super(ResPartnerFADonationReport, self).create(vals)

        # TODO: CHECK if the report can be skipped or if other reports can be skipped
        # TODO: We should also unlink reports skipped or with errors from any submission

        # Update the BPK fields
        res.compute_bpk_fields()

        # Check if there are any report(s) with the same BPK but a different partner
        # HINT: Must be done after compute_bpk_fields()
        reports_with_same_bpk = res._same_bpk_different_partner()
        if reports_with_same_bpk:
            vls = {'state': 'error', 'error_type': 'bpk_not_unique', 'error_code': False,
                   'error_detail': 'Reports with the same private BPK but different Partners:\n%s' %
                                   "\n".join("Report ID: "+str(r.id) for r in reports_with_same_bpk)}
            # TODO: Update all reports_with_same_bpk which are not in state 'submitted' or later
            # Update the current report
            res.write(vls)
            # End processing
            return res

        # TODO: COMPUTE submission fields (e.g.: 'submission_type', 'submission_refnr', ...)

        # TODO: Unlink donation reports from submissions if the state is error or skipped

        # return the record (create it in db)
        return res




    # TODO: OTHER BASIC METHODS
    # @api.multi
    # def write(self, vals):
    #     for r in self:
    #         # TODO: do the same as in create
    #
    # @api.multi
    # def unlink(self):
    #     for r in self:
    #         # TODO: Prevent the unlink of a report if linked to a submission in submitted state
    #
    #
    # # TODO: IMPORTANT: If a BPK of a partner changes donation reports in state submitted or in state error with any
    # #                  other error type than response_error must be flagged with bpk_changed_after_submission
