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

    # HINT: Set by FRST when it creates a cancellation donation report because:
    #           - The BPK of the related partner has changed and a donation report for the old BPK number was already
    #             submitted
    #           - Donation deduction is disabled for the partner after a donation report was already submitted
    cancellation_for_bpk_private = fields.Char(string="Cancellation for Private BPK", readonly=True,
                                               help="Cancellation donation report for last submitted donation report "
                                                    "with this private BPK number")

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
                                        "Uebermittlungsart eindeutig sein. (z.B.: 2017KK222111000-2111000")

    # HINT: If set the BPK forced field values are copied
    submission_firstname = fields.Char(string="Firstname", readonly=True)
    submission_lastname = fields.Char(string="Lastname", readonly=True)
    submission_birthdate_web = fields.Date(string="Lastname", readonly=True)
    submission_zip = fields.Char(string="ZIP Code", readonly=True)
    submission_bpk_request_id = fields.Char(string="BPK Request ID", readonly=True)
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
    # HINT: These fields can only be filled prior to submission because only donation reports without an error
    #       will be submitted. For response errors the fields repsone_error_* are used!
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

    # Set 'ze_datum_von' and 'ze_datum_bis' by 'meldungsjahr' if they are currently empty
    @api.onchange('meldungs_jahr')
    def _onchange_meldungs_jahr(self):
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

    # Only allow to create donation reports for the FinanzOnline Test Environment in the FSON GUI.
    # HINT: Onchange will not be "called" by changes done xmlrpc calls from the sosyncer (TODO Test this ;) )
    @api.onchange('submission_env')
    def _onchange_environment(self):
        for r in self:
            if r.submission_env:
                assert(r.submission_env == "t", _("You can only create donation reports for the 'Test' environment!"))

    # --------------
    # HELPER METHODS
    # --------------
    def _changes_allowed_states(self):
        return 'new', 'disabled', 'error'

    def _changes_allowed_fields_after_submission(self):
        f = ('state',
             'info',
             'submission_id_state',
             'submission_id_datetime',
             'submission_id_url',
             'submission_id_fa_dr_type',
             'response_content',
             'response_error_code',
             'response_error_detail')
        return f

    @api.multi
    def skip_older_unsubmitted_reports(self):
        for r in self:
            # Search for unsubmitted donation reports that are created before this report
            older_reports = r.sudo().search([('submission_env', '=', r.submission_env),
                                             ('bpk_company_id', '=', r.bpk_company_id),
                                             ('partner_id', '=', r.partner_id),
                                             ('meldungs_jahr', '=', r.meldungs_jahr),
                                             ('cancellation_for_bpk_private', '=', r.cancellation_for_bpk_private),
                                             ('state', 'in', r._changes_allowed_states()),
                                             ('anlage_am_um', '<', r.anlage_am_um)])
            # Skip older reports and unlink them from any donation_report.submission
            # HINT: We are already the superuser in this environment
            older_reports.write({'state': 'skipped', 'skipped_by_id': r.id, 'submission_id': False,
                                 'error_type': False, 'error_code': False, 'error_detail': False})

    @api.multi
    def _submission_bpk_private(self):
        assert self.ensure_one(), _("_submission_bpk_private() works only for one record at a time!")

        # Get the private BPK from the cancellation_for_bpk_private field first
        if self.cancellation_for_bpk_private:
            return self.cancellation_for_bpk_private

        # Get it from the donation report if set
        # TODO: Maybe this needs to be disabled ?!?
        # if self.submission_bpk_private:
        #     return self.submission_bpk_private

        # Get it from the currently related bpk record
        bpk = self._get_bpk()
        if bpk:
            return bpk.bpk_private

        # Nothing found so we return False
        return False


    # ATTENTION: Will throw an exception if the found report is the same than 'self'
    @api.multi
    def _last_submitted_report(self):
        assert self.ensure_one(), _("_last_submitted_report() works only for one record at a time!")
        lsr = self.sudo().search([('submission_env', '=', self.submission_env),
                                  ('bpk_company_id', '=', self.bpk_company_id),
                                  ('partner_id', '=', self.partner_id),
                                  ('meldungs_jahr', '=', self.meldungs_jahr),
                                  ('submission_bpk_private', '=', self._submission_bpk_private()),
                                  ('state', 'not in', ['new', 'skipped', 'disabled', 'error'])],
                                 order="anlage_am_um DESC", limit=1)
        if lsr:
            assert lsr.id != self.id, _("_last_submitted_report() This donation report (ID %s) is the latest submitted "
                                        "report! This must be an error! (ID: %s)") % self.id
            assert lsr.state == "response_ok", _("Last submitted donation report  is in state %s but should be "
                                                 "in state 'response_ok'") % (lsr.id, lsr.state)
        return lsr

    @api.multi
    def _get_bpk(self):
        assert self.ensure_one(), _("_get_bpk() works only for one record at a time!")

        bpk = self.env['res.partner.bpk']
        bpk = bpk.sudo().search([('bpk_request_partner_id', '=', self.partner_id),
                                 ('bpk_request_company_id', '=', self.bpk_company_id)])
        if bpk:
            assert len(bpk) == 1, _("More than one BPK Request found for partner %s %s and company %s %s: %s"
                                    "") % (self.partner_id.name, self.partner_id.id,
                                           self.bpk_company_id.name, self.bpk_company_id.id,
                                           " ".join(b.id for b in bpk))

        # Returns either an empty record set or an record set with one record in it
        return bpk

    @api.multi
    def compute_submission_type(self):
        assert self.ensure_one(), _("compute_submission_type() works only for one record at a time!")
        # Cancellation donation report
        # HINT: Since only FSON can submit donation reports FSON must have the last submitted report no matter
        #       if other reports are already be synced or not. Therefore we can compute the submission_type in
        #       FSON.
        if self.betrag <= 0:
            lsr = self._last_submitted_report()
            assert lsr, _("No submitted donation report found for this cancellation donation report "
                          "with the ID %s)!") % self.id
            # HINT: Stonrouebermittlung
            return 'S'

        # Regular donation report
        lsr = self._last_submitted_report()
        return 'A' if lsr else 'E'

    @api.multi
    def compute_submission_refnr(self, submission_bpk_private=False):
        assert self.ensure_one(), _("compute_submission_refnr() works only for one record at a time!")
        # Cancellation donation report
        # ----------------------------
        # HINT: For an cancellation report the submission refnr must be taken from the last submitted report
        # HINT: Since only FSON can submit donation reports FSON must have the last submitted report no matter
        #       if other reports are already synced or not. Therefore we can compute the last submission_refnr in FSON.
        # HINT: refnr example: 2017KK222111000-2111000
        if self.betrag <= 0:
            # HINT: _last_submitted_report() takes into account the 'cancellation_for_bpk_private' field.
            #       So it will return the last donation report based on the correct field.
            lsr = self._last_submitted_report()
            assert lsr, _("No submitted donation report found for this cancellation donation report "
                          "(ID %s)!") % self.id
            return lsr.submission_refnr

        # Regular donation report
        # -----------------------
        refnr = False
        # Find the bpk
        bpk = self._get_bpk()
        if bpk:
            # Get the values for the refnr
            values = (self.meldungs_jahr, self.bpk_company_id.fa_dr_type, self.partner_id.id, bpk.id)
            assert all(values), _("Can not compute submission_refnr because fields are missing! %s") % values
            refnr = "%s%s%s-%s" % (self.meldungs_jahr, self.bpk_company_id.fa_dr_type, self.partner_id.id, bpk.id)

            # Check that the last submitted donation report had the same refnr
            lsr = self._last_submitted_report()
            if lsr:
                assert lsr.submission_refnr == refnr, _("The computed refnr %s for donation report %s is not identical "
                                                        "with the refnr %s of the last submitted donation report %s!"
                                                        "") % (refnr, self.id, lsr.submission_refnr, lsr.id)
        return refnr

    @api.multi
    def compute_report_erstmeldung_id(self, submission_bpk_private=False):
        assert self.ensure_one(), _("compute_report_erstmeldung_id() works only for one record at a time!")
        submission_bpk_private = (submission_bpk_private or
                                  self.cancellation_for_bpk_private or
                                  self.submission_bpk_private)
        erstmeldung = self.sudo().search([('submission_env', '=', self.submission_env),
                                          ('partner_id', '=', self.partner_id),
                                          ('bpk_company_id', '=', self.bpk_company_id),
                                          ('meldungs_jahr', '=', self.meldungs_jahr),
                                          ('submission_bpk_private', '=', self._submission_bpk_private()),
                                          ('submission_type', '=', 'E')])
        if erstmeldung:
            assert len(erstmeldung) == 1, _("More than one Erstmeldung found for donation report %s !") % self.id

        return erstmeldung.id if erstmeldung else False

    @api.multi
    def update_state_and_submission_information(self):
        for r in self:
            # Skipp older unsubmitted reports
            r.skip_older_unsubmitted_reports()

            # Avoid any changes to this report if it was skipped or submitted!
            if r.state not in self._changes_allowed_states():
                continue

            # Skip this report if newer reports exists already because of sosync LIFO!
            # HINT: It was already checked above that this report is in a state where changes are allowed.
            newer = r.sudo().search([('submission_env', '=', r.submission_env),
                                     ('partner_id', '=', r.partner_id),
                                     ('bpk_company_id', '=', r.bpk_company_id),
                                     ('meldungs_jahr', '=', r.meldungs_jahr),
                                     ('cancellation_for_bpk_private', '=', r.cancellation_for_bpk_private),
                                     ('anlage_am_um', '>', r.anlage_am_um)],
                                    order="anlage_am_um DESC", limit="1")
            if newer:
                r.write({'state': 'skipped', 'skipped_by_id': newer.id, 'submission_id': False,
                         'error_type': False, 'error_code': False, 'error_detail': False})
                continue

            # Check the BPK
            # -------------
            # Donation deduction is disabled
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
            bpk = r._get_bpk()
            if not bpk:
                logger.error('update_state_and_submission_information(): BPK not found but expected! '
                             'Partner %s (ID %s) Donation Report ID: %s' % (r.partner_id.name, r.partner_id.id, r.id))
                r.write({'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                         'error_type': 'bpk_missing', 'error_code': False,
                         'error_detail': "BPK not found but expected!"})
                continue

            # Check if there are any other reports with the same bpk but a different partner
            # ------------------------------------------------------------------------------
            # ATTENTION: Such partners must be merged before the donation report can be submitted
            # HINT: It is ok if there are donation reports for the same partner with different bpk numbers
            if r.cancellation_for_bpk_private or bpk.bpk_private:
                # Build the search domain (same company but different partners)
                domain = [('bpk_request_company_id', '=', r.bpk_company_id),
                          ('bpk_request_partner_id', '!=', r.partner_id)]
                if r.cancellation_for_bpk_private:
                    domain.append(('cancellation_for_bpk_private', '=', r.cancellation_for_bpk_private))
                else:
                    domain.append(('submission_bpk_public', '=', bpk.bpk_public))

                # Search for donation reports with different partner but the same BPK number
                r_same_bpk = r.sudo().search(domain)

                # If donation reports are found set them and this report to state 'error'
                if r_same_bpk:
                    error_detail = _("Reports found with the same BPK but a different Partner:\n"
                                     "%s") % "\n".join("Report ID: "+str(rep.id) for rep in (r | r_same_bpk))
                    rvals = {'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                             'error_type': 'bpk_not_unique', 'error_code': False, 'error_detail': error_detail}
                    # Update this report
                    r.write(rvals)
                    # Update other reports if possible
                    for report_same_bpk in r_same_bpk:
                        if report_same_bpk.state in self._changes_allowed_states():
                            report_same_bpk.write(rvals)
                    continue

            # Compute the submission values
            # -----------------------------
            # HINT: If cancellation_for_bpk_private is set we need the values from the related bpk request
            subm_vals = {
                'submission_type': r.compute_submission_type(),
                'submission_refnr': r.compute_submission_refnr(),
                'report_erstmeldung_id': r.compute_report_erstmeldung_id(),
                #
                'submission_firstname': False if r.cancellation_for_bpk_private else bpk.bpk_request_firstname,
                'submission_lastname': False if r.cancellation_for_bpk_private else bpk.bpk_request_lastname,
                'submission_birthdate_web': False if r.cancellation_for_bpk_private else bpk.bpk_request_birthdate,
                'submission_zip': False if r.cancellation_for_bpk_private else bpk.bpk_request_zip,
                #
                'submission_bpk_request_id': False if r.cancellation_for_bpk_private else bpk.id,
                'submission_bpk_public': False if r.cancellation_for_bpk_private else bpk.bpk_public,
                'submission_bpk_private': r.cancellation_for_bpk_private or bpk.bpk_private,
                #
                # TODO: start the debugger and see if field names are in _fields :)
                #'submission_sosync_fs_id': r.sosync_fs_id if 'sosync_fs_id' in r._fields else False,
            }

            # Check if all needed values are available
            # ----------------------------------------
            if r.cancellation_for_bpk_private:
                mandatory_submission_fields = ('submission_type', 'submission_refnr', 'cancellation_for_bpk_private')
            else:
                mandatory_submission_fields = ('submission_type',
                                               'submission_refnr',
                                               'submission_firstname',
                                               'submission_lastname',
                                               'submission_birthdate_web',
                                               'submission_bpk_request_id',
                                               'submission_bpk_public',
                                               'submission_bpk_private')
            missing_fields = (field for field in mandatory_submission_fields if not subm_vals[field])
            if missing_fields:
                r.write({'state': 'error', 'skipped_by_id': False, 'submission_id': False,
                         'error_type': 'data_incomplete', 'error_code': False,
                         'error_detail': 'Missing Fields: %s' % str(missing_fields)})
                continue

            # Update the donation report with the computed values
            # ---------------------------------------------------
            values = {'state': 'new', 'skipped_by_id': False, 'submission_id': r.submission_id,
                      'error_type': False, 'error_code': False, 'error_detail': False}
            values.append(subm_vals)
            r.write(values)
            continue

    # ------------
    # CRUD METHODS
    # ------------
    @api.model
    def create(self, vals):
        # Create the donation report in the current environment (=memory only right now)
        # ATTENTION: 'self' is still empty but the record 'exits' in the 'res' recordset already so every change
        #            or method call must be done to res and not to self
        # Other stuff done by the in memory creation:
        #     - api.constrain(s) = Values validation
        res = super(ResPartnerFADonationReport, self).create(vals)

        # Compute the state
        # HINT: Will also compute and write the submission values if state is not 'skipped', 'disabled' or 'error'
        res.update_state_and_submission_information()

        # Return the record (create it in db)
        return res

    @api.multi
    def write(self, vals):
        for r in self:
            # Prevent an FinanzOnline environment change after the donation report got created.
            if 'submission_env' in vals and vals['submission_env'] != r.submission_env:
                raise ValidationError(_("You can not change the environment once the donation report got created!"))

            # Prevent any changes to the basic fields after submission
            if r.state not in self._changes_allowed_states():
                changes_allowed_fields = self._changes_allowed_fields_after_submission()
                if any(vals[field] != r[field] for field in vals if field not in changes_allowed_fields):
                    raise ValidationError(_("Changes to some of the fields in %s are only allowed in the states %s!")
                                          % (vals, str(self._changes_allowed_states())))

        # ATTENTION: After this 'self' is changed in memory and 'res' is only a boolean !
        res = super(ResPartnerFADonationReport, self).write(vals)

        # Compute the state
        # HINT: Will also compute and write the submission values if in unsubmitted states
        if 'state' not in vals:
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
