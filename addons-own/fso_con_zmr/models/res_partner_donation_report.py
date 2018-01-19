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
                                        ('disabled', 'Donation Deduction Disabled'),
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

    # Data for submission (normally from Fundraising Studio if not a test environment report)
    # ---------------------------------------------------------------------------------------
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

    # # BPK request
    # # DISABLED because FRST will do the check! and here the submission_bpk_public and submission_bpk_private is enough
    # # -----------
    # bpk_id = fields.Many2one(string="Partner/Company BPK", comodel_name='res.partner.bpk', readonly=True)
    # bpk_state = fields.Selection(string="BPK State", readonly=True)
    # bpk_public = fields.Char(string="BPK Public", readonly=True)
    # bpk_private = fields.Char(string="BPK Private", readonly=True)

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
                                  selection=[('bpk_pending', 'BPK Request Pending'),
                                             ('bpk_missing', 'BPK Not Found'),
                                             ('bpk_not_unique', 'BPK Not Unique'),     # multiple partners with same bpk
                                             ('data_incomplete', 'Data Incomplete'),   # should never happen!
                                             ])
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

    # TODO: Add various api constrains e.g.: for mandatory fields or that fields can not be changed in certain states
    # TODO: Add an api constrain that the environment is not allowed to change

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
        assert self.ensure_one(), _("_same_bpk_different_partner() works only for one record at a time!")
        if not self.bpk_private:
            return self.env['res.partner.donation_report']
        # Find donation reports with the same bpk and company but with a different partner
        duplicates = self.sudo().search([('bpk_private', '=', self.bpk_private),
                                         ('bpk_request_company_id', '=', self.bpk_company_id),
                                         ('bpk_request_partner_id', '!=', self.partner_id)],
                                         ('bpk_public_forced', '=', self.bpk_public_forced))
        return duplicates

    def _changes_allowed_states(self):
        return 'new', 'disabled', 'error'

    def _mandatory_submission_fields(self):
        mandatory_submission_fields = ('submission_type', 'submission_refnr',
                                       'submission_firstname', 'submission_lastname', 'submission_birthdate_web')
        return mandatory_submission_fields

    @api.multi
    def skip_older_unsubmitted_reports(self):
        for report in self:
            # Search for unsubmitted donation reports that are created before this report
            older_reports = report.sudo().search([('bpk_company_id', '=', self.bpk_company_id),
                                                  ('partner_id', '=', self.partner_id),
                                                  ('meldungs_jahr', '=', self.meldungs_jahr),
                                                  ('bpk_public_forced', '=', self.bpk_public_forced),
                                                  ('state', 'in', self._changes_allowed_states()),
                                                  ('anlage_am_um', '<', self.anlage_am_um)])
            # Skip older reports and unlink them from any donation_report.submission
            # HINT: we are already the superuser in this environment
            older_reports.write({'state': 'skipped', 'skipped_by_id': report.id, 'submission_id': False,
                                 'error_type': False, 'error_code': False, 'error_detail': False})

    def update_state_and_submission_information(self):
        for r in self:
            # Skipp older reports
            # TODO: correct domain for bpk_public_forced see below :)
            r.skip_older_unsubmitted_reports()

            # Ignore submitted and skipped donation reports
            # ATTENTION: They must stay unchanged! (TODO: Add an api.constraint)
            if r.state not in self._changes_allowed_states():
                continue

            # Check the BPK
            submission_bpk_public = False
            submission_bpk_private = False

            # Donation Deduction is disabled
            if r.partner_id.bpk_state == 'disabled':
                r.write({'state': 'disabled', 'skipped_by_id': False, 'submission_id': False,
                         'error_type': False, 'error_code': False, 'error_detail': False})
                continue
            # BPK request pending
            if r.partner_id.bpk_state == 'pending':
                r.write({'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                         'error_type': 'bpk_pending', 'error_code': False, 'error_detail': False})
                continue
            # BPK NOT found
            if r.partner_id.bpk_state != 'found':
                r.write({'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                         'error_type': 'bpk_missing', 'error_code': False, 'error_detail': False})
                continue

            # Find the related BPK request
            bpk = self.env['res.partner.bpk']
            bpk = bpk.sudo().search([('bpk_request_partner_id', '=', r.partner_id),
                                     ('bpk_request_company_id', '=', r.bpk_company_id)])
            if len(bpk) == 1:
                submission_bpk_public = bpk.bpk_public
                submission_bpk_private = bpk.bpk_private
            else:
                logger.error('update_state_and_submission_information(): BPK not found but expected! '
                             'Partner %s (ID %s) Donation Report ID: %s' % (r.partner_id.name, r.partner_id.id, r.id))
                r.write({'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                         'error_type': 'bpk_missing', 'error_code': False,
                         'error_detail': "BPK not found or multiple found! (Number of BPK found: %s)" % len(bpk)})
                continue

            # Check if there are any other reports with the same bpk but a different partner
            # ATTENTION: Such partners must be merged before the donation report can be submitted
            if r.bpk_public_forced or submission_bpk_private:
                domain = [('bpk_request_company_id', '=', r.bpk_company_id),
                          ('bpk_request_partner_id', '!=', r.partner_id)]
                if r.bpk_public_forced:
                    domain.append(('bpk_public_forced', '=', r.bpk_public_forced))
                else:
                    domain.append(('submission_bpk_public', '=', submission_bpk_public))
                # Search for donation reports with different partner but the same BPK number
                r_same_bpk = r.sudo().search(domain)
                if r_same_bpk:
                    error_detail = _("Reports found with the same BPK but a different Partner:\n"
                                     "%s") % "\n".join("Report ID: "+str(rep.id) for rep in (r | r_same_bpk))
                    rvals = {'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                             'error_type': 'bpk_not_unique', 'error_code': False, 'error_detail': error_detail}
                    r.write(rvals)
                    for report_same_bpk in r_same_bpk:
                        if report_same_bpk.state in self._changes_allowed_states():
                            report_same_bpk.write(rvals)
                    continue

            # TODO: Compute and update the submission values
            subm_vals = {
                'submission_type': False,
                'submission_refnr': False,
                'report_erstmeldung_id': False,
                #
                'submission_firstname': False,
                'submission_lastname': False,
                'submission_birthdate_web': False,
                'submission_zip': False,
                'submission_bpk_public': False if r.bpk_public_forced else submission_bpk_public,
                'submission_bpk_private': False if r.bpk_public_forced else submission_bpk_private,
                'submission_sosync_fs_id': False,
            }

            # Check if all needed values are available
            mandatory_submission_fields = ('submission_type', 'submission_refnr',
                                           'submission_firstname', 'submission_lastname', 'submission_birthdate_web')
            if not r.bpk_public_forced:
                mandatory_submission_fields = mandatory_submission_fields + ('submission_bpk_public',
                                                                             'submission_bpk_private')
            missing_fields = (field for field in mandatory_submission_fields if not subm_vals[field])
            if missing_fields:
                r.write({'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                         'error_type': 'data_incomplete', 'error_code': False,
                         'error_detail': 'Missing Fields: %s' % str(missing_fields)})
                continue

            # Update the donation report with the computed values
            values = {'state': 'new', 'skipped_by_id': False, 'submission_id': r.submission_id,
                      'error_type': False, 'error_code': False, 'error_detail': False}
            values.append(subm_vals)
            r.write(values)
            continue


    @api.model
    def create(self, vals):
        # Create the donation report in the current environment (=memory only right now)
        # ATTENTION: 'self' is still empty but the record 'exits' in the 'res' recordset already so every change
        #            or method call must be done to res and not to self
        # Other stuff done by the in memory creation:
        #     - api.constrain(s) = Values validation
        res = super(ResPartnerFADonationReport, self).create(vals)

        # Compute the state and update the submission values if state is not 'disabled' or 'error'
        res.update_state_and_submission_information()

        # Return the record (create it in db)
        return res

    @api.multi
    def write(self, vals):
        for r in self:
            # Prevent an environment change after the donation got created
            if 'submission_env' in vals and vals['submission_env'] != r.submission_env:
                raise ValidationError(_("You can not change the environment once the donation report got created!"))

        # ATTENTION: !!! After this 'self' is changed (in memory i guess) 'res' is only a boolean !!!
        res = super(ResPartnerFADonationReport, self).write(vals)

        # Compute the state and update the submission values if state is not 'disabled' or 'error'
        self.update_state_and_submission_information()

        # Return the recordset
        return res

    @api.multi
    def unlink(self):
        for r in self:
            if r.state not in self._changes_allowed_states():
                raise ValidationError(_("Deletion of a donation report is only allowed in the states "
                                        "%s") % self._changes_allowed_states())
        return super(ResPartnerFADonationReport, self).unlink()
