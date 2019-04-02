# -*- coding: utf-8 -*-
import openerp
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, SUPERUSER_ID
from openerp.addons.fso_base.tools.datetime_tools import naive_to_timezone

import time
import datetime
import pytz
import hashlib

import logging
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


# Austrian Finanzamt Donation Reports (Spendenberichte pro Person fuer ein Jarh)
class ResPartnerFADonationReport(models.Model):
    _name = 'res.partner.donation_report'
    _rec_name = 'id'

    # HINT: create_date is added to make sure the order of the records in the XML stays the same in prepare() even
    #       if anlage_am_um is the same for multiple records
    _order = 'partner_id, anlage_am_um DESC, create_date DESC'

    # Create combined index for faster tree view
    def _auto_init(self, cr, context=None):
        res = super(ResPartnerFADonationReport, self)._auto_init(cr, context=context)
        cr.execute('SELECT indexname FROM pg_indexes '
                   'WHERE indexname = \'res_partner_donation_report_partner_id_anlage_am_um_create_date_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX res_partner_donation_report_partner_id_anlage_am_um_create_date_index '
                       'ON res_partner_donation_report (partner_id, anlage_am_um DESC, create_date DESC)')
        return res

    # DISABLED: too slow!
    #_inherit = ['mail.thread']

    now = fields.datetime.now

    # ------
    # FIELDS
    # ------
    # Add an index to create_date
    create_date = fields.Datetime(index=True)

    # HINT: 'fields' can only be changed in FS-Online in state 'new'
    # ATTENTION: The 'error' state is only for errors prior to any submission!!! e.g.: bpk_missing
    state = fields.Selection(string="State", readonly=True, default='new', track_visibility='onchange',
                             selection=[('new', 'New'),
                                        ('skipped', 'Skipped'),
                                        ('disabled', 'Donation Deduction Disabled'),
                                        ('error', 'Error'),
                                        ('submitted', 'Submitted to FinanzOnline'),
                                        ('response_ok', 'Accepted by FinanzOnline'),
                                        ('response_nok', 'Rejected by FinanzOnline'),
                                        ('unexpected_response', 'Unexpected Response')],
                             index=True)

    # NEW field e.g.: for initial data acquisition
    imported = fields.Boolean(string='Imported', readonly=True,
                              help='Imported Donation Report! If "True" most contrains will be IGNORED and '
                                   'some fields like "submission_type" will NOT be computed!')

    # TODO: Make sure BPK will take donation reports of type donor_instruction into account !!!
    # TODO: Make sure donation reports can not be submitted if last DR with donnor_instruction=submission_forbidden !!!
    # NEW field to mark "pseudo" donation reports which only show/store the command of the donor for a specific
    # fiscal year. E.g. These explicit command of the donor is more important than the OptOut group except for the
    # system group where we mark persons that can never submit donations.
    donor_instruction = fields.Selection(string="Donor Instruction", index=True,
                                         selection=[('submission_forced', 'Submission forced'),
                                                    ('submission_forbidden', 'Submission forbidden')],
                                         help="Explicit command from the donor to submit or forbid donation report "
                                              "submission for this fiscal year and organization. This has a higher "
                                              "importance than the OptOut group.")
    donor_instruction_info = fields.Char(string="Donor Instruction Info",
                                         help="Information how and when the donor gave an explicit instruction for a "
                                              "fiscal year")

    # Reason why a donation report was created.This may help organisations to decide whether or not to manually submit
    # a donation report for the years after the automatic submission.
    create_reason = fields.Selection(string="Create Reason", readonly=True, track_visibility='onchange',
                                     selection=[('regular', 'Regular Report'),
                                                ('amount_changed', 'Donation-Amount changed'),
                                                ('bpk_changed', 'BPK-Number changed'),
                                                ('bpk_manual_cancellation', 'BPK after manual cancellation'),
                                                ('access_data', 'Changed ZMR/FinanzOnline access data'),
                                                ('grp_bpkoptout_removed', 'OptOut Group removed'),
                                                ('grp_systemdenied_removed', 'System-Denied Group removed'),
                                                ('err_u_008', 'Report after Error ERR-U-008'),
                                                ('err_u_006', 'Report after Error ERR-U-006'),
                                                ('err_u_007', 'Report after Error ERR-U-007'),
                                                ('user_resubmission', 'Resubmission by user request'),
                                                ('submission_forced', 'Donor instructed to force submission'),
                                                # Cancellation
                                                ('c_amount_zero', 'Amount dropped to zero'),
                                                ('c_grp_bpkoptout_added', 'OptOut-Group added'),
                                                ('c_grp_systemdenied_added', 'System-Denied-Group added'),
                                                ('c_bpk_changed', 'BPK changed'),
                                                ('c_err_u_008', 'Cancellation to fix error ERR-U-008'),
                                                ('c_err_u_006', 'Cancellation to fix error ERR-U-006'),
                                                ('c_err_u_007', 'Cancellation to fix error ERR-U-007'),
                                                ('c_user_resubmission', 'Prepare for resubmission by user request'),
                                                ('c_submission_forbidden', 'Donor instructed to forbid submission'),
                                                ])

    # Error before submission
    # -----------------------
    # HINT: These fields can only be filled prior to submission because only donation reports without an error
    #       will be submitted. For response errors the fields response_error_* are used!
    error_type = fields.Selection(string="Error Type", readonly=True, track_visibility='onchange',
                                  selection=[('bpk_pending', 'BPK Request Pending'),
                                             ('bpk_missing', 'BPK Not Found'),
                                             ('bpk_not_unique', 'BPK Not Unique'),     # multiple partners with same bpk
                                             ('data_incomplete', 'Data Incomplete'),   # should only happen if comp. data missing
                                             ('nok_released', 'Released from rejected Submission (NOK)'),
                                             ('zero_but_lsr', 'Donations are already submitted'),
                                             ('zero_lsr_exception', 'Last submitted report exception'),
                                             ('company_data_changed', 'Company Data Changed'),
                                             ])
    error_code = fields.Char(string="Error Code", readonly=True)
    error_detail = fields.Text(string="Error Detail", readonly=True, track_visibility='onchange')

    # Erstmeldung link
    # ----------------
    # Erstmeldung
    report_erstmeldung_id = fields.Many2one(string="Zugehoerige Erstmeldung", track_visibility='onchange',
                                            comodel_name='res.partner.donation_report', readonly=True)
    # Follow Up reports to this Erstmeldung
    report_follow_up_ids = fields.One2many(string="Follow-Up Reports", comodel_name="res.partner.donation_report",
                                           inverse_name="report_erstmeldung_id", readonly=True)
    # Skipped link
    # ------------
    # Skipped by donation report
    skipped_by_id = fields.Many2one(string="Skipped by Report", comodel_name='res.partner.donation_report',
                                    readonly=True)
    # This report skipped these donation reports
    skipped = fields.One2many(string="Skipped the Reports", comodel_name="res.partner.donation_report",
                              inverse_name="skipped_by_id", readonly=True)

    # Cancelled link (betrag 0)
    # -------------------------
    # The last submitted report that should be cancelled by this cancellation donation report
    cancelled_lsr_id = fields.Many2one(string="Cancelled Last Submitted Report",
                                       comodel_name='res.partner.donation_report',
                                       readonly=True)
    # The cancellation donation report(s) that cancelled this regular report
    cancelled_by_ids = fields.One2many(string="Cancelled by Report(s)",
                                       comodel_name="res.partner.donation_report",
                                       inverse_name="cancelled_lsr_id", readonly=True)

    # Data for submission
    # -------------------
    # HINT: Data from FRST if not a test environment donation report
    # ATTENTION: This will determine the submission url!
    submission_env = fields.Selection(string="FinanzOnline Environment", selection=[('T', 'Test'), ('P', 'Production')],
                                      default="T", required=True, readonly=True, states={'new': [('readonly', False)]},
                                      track_visibility='onchange',
                                      index=True)
    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner',  required=True,
                                 track_visibility='onchange',
                                 readonly=True, states={'new': [('readonly', False)]},
                                 index=True)
    bpk_company_id = fields.Many2one(string="BPK Company", comodel_name='res.company',  required=True,
                                     track_visibility='onchange',
                                     readonly=True, states={'new': [('readonly', False)]},
                                     index=True)
    anlage_am_um = fields.Datetime(string="Generated at", required=True,
                                   help=_("Donation Report generation date and time. This is used for the order of the "
                                          "submission_type computation! Must include all donations available at this "
                                          "date and time that fall inside ze_datum_von and ze_datum_bis"),
                                   readonly=True, states={'new': [('readonly', False)]},
                                   index=True)
    ze_datum_von = fields.Datetime(string="Includes donations from", required=True,
                                   readonly=True, states={'new': [('readonly', False)]})
    ze_datum_bis = fields.Datetime(string="Includes donations to", required=True,
                                   help=_("Includes all donations up to this date-time which are "
                                          "available at the time the report is generated (anlage_am_um)."),
                                   readonly=True, states={'new': [('readonly', False)]})
    meldungs_jahr = fields.Selection(string="Year", required=True,
                                     track_visibility='onchange',
                                     help=_("Donation deduction year (Meldejahr)"),
                                     readonly=True, states={'new': [('readonly', False)]},
                                     selection=[(str(i), str(i)) for i in range(2017, int(now().year)+11)],
                                     index=True)
    betrag = fields.Float(string="Total", required=True,
                          track_visibility='onchange',
                          help=_("Donation deduction total (Betrag)"),
                          readonly=True, states={'new': [('readonly', False)]})
    # HINT: Set by FRST when it creates a cancellation donation report because:
    #           - The BPK of the related partner has changed and a donation report for the old BPK number was already
    #             submitted
    #           - Donation deduction is disabled for the partner after a donation report was already submitted
    cancellation_for_bpk_private = fields.Char(string="Cancellation for Private BPK", readonly=True,
                                               track_visibility='onchange',
                                               help="Cancellation donation report for last submitted donation report "
                                                    "with this private BPK number",
                                               index=True)
    # Optional field for extra information from FRST
    info = fields.Text(string="Info", readonly=True)

    # Force submission (only set in FRST NOT in FSON!)
    # HINT: Used for user requested manual resubmission of a donation report!
    #       TODO: Must be submitted by scheduled_submission() even if outside of Meldezeitraum!
    force_submission = fields.Boolean(string="Force Submission", readonly=True,
                                      help="Will be submitted to FinazOnline by scheduler even if outside of automatic "
                                           " submission range! (Meldezeitraum)")

    # Fields computed (or recomputed) just before submission to FinanzOnline
    # ----------------------------------------------------------------------
    submission_type = fields.Selection(string="Type", readonly=True,
                                       track_visibility='onchange',
                                       selection=[('E', 'Erstuebermittlung'),
                                                  ('A', 'Aenderungsuebermittlung'),
                                                  ('S', 'Stornouebermittlung')])

    # ATTENTION: Follow-Up Reports of type A or S will share the same number
    # Format: D(for Dadi)-[meldungs_jahr]-[fa_dr_type]-[partner_id.id]
    submission_refnr = fields.Char(string="Reference Number (RefNr)", readonly=True, size=23,
                                   track_visibility='onchange',
                                   help="Die RefNr muss pro Uebermittler, Jahr und "
                                        "Uebermittlungsart eindeutig sein. (z.B.: 2017KK222111000-2111000",
                                   index=True)
    # HINT: If set the BPK forced field values are copied
    submission_bpk_request_id = fields.Char(string="BPK Request ID", readonly=True)
    submission_bpk_public = fields.Text(string="Public BPK (vbPK)", readonly=True, track_visibility='onchange')
    submission_bpk_private = fields.Char(string="Private BPK", readonly=True, track_visibility='onchange',
                                         index=True)
    submission_firstname = fields.Char(string="Firstname", readonly=True)
    submission_lastname = fields.Char(string="Lastname", readonly=True, track_visibility='onchange')
    submission_birthdate_web = fields.Date(string="Birthdate Web", readonly=True)
    submission_zip = fields.Char(string="ZIP Code", readonly=True)

    # Additional BPK Info
    submission_bpk_state = fields.Char(string="Partner BPK-State", readonly=True)
    submission_dd_disabled = fields.Char(string="Donation Deduction Disabled", readonly=True)
    submission_dd_optout = fields.Char(string="Donation Deduction OptOut", readonly=True)

    # NEW: Add the request date to make it easy to compare "donation report create_date", "bpk_request_date" and
    #      "donation report submission date". Handy if a report is send long after it's creation.
    submission_bpk_request_date = fields.Char(string="BPK Request Date", readonly=True)

    # Donation report submission link and information
    # -----------------------------------------------
    submission_id = fields.Many2one(string="Submission",
                                    help="submission_id.id is used as the MessageRefId !",
                                    comodel_name="res.partner.donation_report.submission",
                                    domain="[('state','in',('new','prepared','error'))]",
                                    readonly=True, states={'new': [('readonly', False)]},
                                    track_visibility='onchange',
                                    index=True)
    # HINT: This is the datetime of the (latest) submission (try) to FinanzOnline
    # HINT: Will be updated by the donation report submission when the status changes to
    #       submitted or any response status together with the state change
    submission_id_datetime = fields.Datetime(string="Submission Datetime", readonly=True,
                                             index=True)

    # Related Fields from the donation report submission (drs)
    # TODO: REMOVE related fields -> must change the last_submitted_report computation for this!
    # submission_id_state = fields.Selection(string="Submission State",
    #                                        related="submission_id.state", store=True, readonly=True)
    # submission_id_datetime = fields.Datetime(string="Submission Datetime",
    #                                          related="submission_id.submission_datetime", store=True,  readonly=True)
    # submission_id_url = fields.Char(string="Submission URL",
    #                                 related="submission_id.submission_url", store=True,  readonly=True)
    # submission_id_fa_dr_type = fields.Char(string="Submission OrgType",
    #                                        related="submission_id.submission_fa_dr_type", store=True,  readonly=True)

    # FinanzOnline XML Response
    # -------------------------
    # HINT: response_content will only hold the xml snippets related to this donation report based on submission_refnr
    response_content = fields.Text(string="Response Content", readonly=True)
    response_error_code = fields.Char(string="Response Error Code", readonly=True, track_visibility='onchange',
                                      index=True)
    response_error_detail = fields.Text(string="Response Error Detail", readonly=True, track_visibility='onchange')
    response_error_orig_refnr = fields.Char(string="Response ERR-U-008 orig. RefNr",
                                            help="The last submitted report was rejected with an ERR-U-008. This means "
                                                 "the report was rejected because an Erstmeldung existed already in "
                                                 "FinanzOnline. This happens if donation reports are submitted "
                                                 "manually by the organisation or by other service providers.",
                                            readonly=True, track_visibility='onchange',
                                            index=True)

    # ----------
    # CONSTRAINS
    # ----------
    @api.constrains('meldungs_jahr', 'betrag', 'ze_datum_von', 'ze_datum_bis',
                    'anlage_am_um', 'submission_env', 'bpk_company_id', 'cancellation_for_bpk_private',
                    'submission_id')
    def _check_submission_data_constrains(self):
        now = datetime.datetime.now()
        min_year = 2017
        max_year = int(now.year)+1

        for r in self:

            # Make sure none of this fields are changed if it is already submitted for non imported reports
            if not r.imported:
                if r.state and r.state not in list(r._changes_allowed_states()) + ['skipped']:
                    raise ValidationError(_("Changes to report (ID %s) not allowed in state: %s") % (r.id, r.state))

            # Make sure it is impossible to change the submission_id to an already submitted submission
            if r.submission_id and r.submission_id.state not in ('new', 'prepared', 'error'):
                raise ValidationError(_("Adding a report (ID %s) to a submission (ID %s) in state '%s' is not allowed!"
                                        "") % (r.id, r.submission_id.id, r.submission_id.state))

            # Make sure the Submission fits the report
            if r.submission_id and (r.submission_env != r.submission_id.submission_env
                                    or r.meldungs_jahr != r.submission_id.meldungs_jahr
                                    or r.bpk_company_id != r.submission_id.bpk_company_id):
                raise ValidationError(_("Adding report (ID %s) to submission (ID %s) is not allowed because"
                                        "'submission_env' or 'meldungs_jahr' or 'bpk_company_id' do not match!"
                                        "") % (r.id, r.submission_id.id))

            # Check year (meldungs_jahr)
            if not r.meldungs_jahr or int(r.meldungs_jahr) < min_year or int(r.meldungs_jahr) > max_year:
                raise ValidationError(_("Year must be inside %s - %s") % (min_year, max_year))

            # Check total (betrag) is not negative
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
                #print r.ze_datum_von
                if von < year_start or bis > year_end:
                    raise ValidationError(_("Report range seems to be outside of the report year %s! "
                                            "Please check ze_datum_von and ze_datum_bis."
                                            "") % (r.ze_datum_von, r.ze_datum_bis, r.meldungs_jahr))

    @api.constrains('donor_instruction', 'donor_instruction_info', 'state')
    def _constrain_donor_instruction(self):
        for r in self:
            if r.donor_instruction:
                if not r.donor_instruction_info or r.state != 'skipped' or not r.anlage_am_um or any(
                        r[f] for f in ('imported', 'force_submission',
                                       'cancelled_lsr_id', 'cancellation_for_bpk_private', 'submission_bpk_private',
                                       'submission_type', 'submission_refnr', 'submission_id')):
                    raise ValidationError(_("Reports with 'donor_instruction' set must be in state 'skipped' and the"
                                            "field 'donor_instruction_info' must be filled!"))
            else:
                if r.donor_instruction_info:
                    raise ValidationError(_("'donor_instruction_info' must be empty if 'donor_instruction' is not set"))

    # --------
    # ONCHANGE (WEB GUI ONLY)
    # --------
    # Set 'ze_datum_von' and 'ze_datum_bis' by 'meldungsjahr' if they are currently empty
    @api.onchange('meldungs_jahr')
    def _onchange_meldungs_jahr(self):
        vtz = pytz.timezone("Europe/Vienna")
        for r in self:
            if r.meldungs_jahr:
                if not r.anlage_am_um:
                    r.anlage_am_um = fields.datetime.now()
                if not r.ze_datum_von:
                    year_start = datetime.datetime(int(r.meldungs_jahr), 01, 01, 00, 00, 00)
                    year_start = naive_to_timezone(naive=year_start, naive_tz=vtz, naive_dst=True, target_tz=pytz.UTC)
                    r.ze_datum_von = year_start
                if not r.ze_datum_bis:
                    year_end = datetime.datetime(int(r.meldungs_jahr), 12, 31, 23, 59, 59, 999)
                    year_end = naive_to_timezone(naive=year_end, naive_tz=vtz, naive_dst=True, target_tz=pytz.UTC)
                    r.ze_datum_bis = year_end

    # Only allow to create donation reports for the FinanzOnline Test Environment in the FSON GUI.
    # HINT: Onchange will not be "called" by changes done xmlrpc calls from the sosyncer
    @api.onchange('submission_env')
    def _onchange_environment(self):
        for r in self:
            if r.submission_env != "T":
                r.submission_env = "T"

    # --------------
    # HELPER METHODS
    # --------------
    def _changes_allowed_states(self):
        return 'new', 'disabled', 'error'

    def _changes_allowed_fields_after_submission(self):
        f = ('state',
             'info',
             'submission_id_datetime',
             'response_content',
             'response_error_code',
             'response_error_detail',
             'response_error_orig_refnr',)
        return f

    @api.multi
    def _get_bpk(self):
        assert self.ensure_one(), _("_get_bpk() works only for one record at a time!")

        bpk = self.env['res.partner.bpk']
        bpk = bpk.sudo().search([('bpk_request_partner_id', '=', self.partner_id.id),
                                 ('bpk_request_company_id', '=', self.bpk_company_id.id)])

        # Check for more than one BPK Request per partner/company
        if bpk:
            if len(bpk) > 1:
                msg = _("More than one BPK Request found for partner %s %s and company %s %s: %s"
                        "") % (self.partner_id.name, self.partner_id.id,
                               self.bpk_company_id.name, self.bpk_company_id.id,
                               "".join("BPK-ID: %s, " % str(b.id) for b in bpk))
                logger.error(msg)
                try:
                    logger.info(_("Try to correct the BPK Requests for partner %s (ID %s)"))
                    # Force the BPK request
                    # HINT: This is save because set_bpk() will recalculate the partner bpk-state first
                    self.partner_id.sudo().set_bpk()
                    # Recursively call _get_bpk() again
                    bpk = self._get_bpk()
                except Exception as e:
                    logger.error(repr(e))
                    raise ValidationError(msg)

        # Returns either an empty record set or an record set with one record in it
        return bpk

    @api.multi
    def last_submitted_report(self, submission_bpk_private='ignore'):
        """
        Returns the last successfully submitted donation report
        OR the last submitted donation report with an 'ERR-U-008' error which means that there was already an
        'Erstmeldung' for this donation report (e.g.: if the customer did a manual 'Spendenmeldung' in FinanzOnline)

        Throws an exception if the submission state of the last submitted report is not response_ok!

        If a cancellation report and a regular report are submitted in the same submission the
        anlage_am_um datetime of the regular report (betrag > 0) must be higher than the one of the cancellation
        reports! Therefore lsr can only be return a cancellation report if no regular report was in the last
        submission or if submission_bpk_private is given!

        ATTENTION: It should be IMPOSSIBLE that there are two regular donation reports for one person in the same
                   submission (because all but one regular reports must have been skipped!). There may be a
                   cancellation report and a regular report on the same submission but then the regular report MUST
                   be AFTER the cancellation report(s) in the XML! This is ordered by anlage_am_um.

        :return: donation report record set witch exactly one record or no record
        """
        assert self.ensure_one(), _("last_submitted_report() works only for one record at a time!")

        # HINT: Since imported donation reports have no submission_id we can not use it in the domain!
        domain = [('submission_env', '=', self.submission_env),
                  ('bpk_company_id', '=', self.bpk_company_id.id),
                  ('partner_id', '=', self.partner_id.id),
                  ('meldungs_jahr', '=', self.meldungs_jahr),
                  ('state', '!=', False),
                  ('state', 'not in', ['new', 'skipped', 'disabled', 'error']),
                  #('submission_id', '!=', False),
                  #('submission_id_datetime', '!=', False),
                  ('id', '!=', self.id)]

        # ATTENTION: If submission_bpk_private is set the lsr FOR THIS BPK will be returned!
        if submission_bpk_private != 'ignore':
            domain += [('submission_bpk_private', '=', submission_bpk_private)]

        # ATTENTION: Make sure the inverse order is used for the XML record generation in the submission!
        # HINT: Since imported donation reports have no submission_id_datetime we can not use it for the sort order!
        # lsr = self.sudo().search(domain,
        #                          order="submission_id_datetime DESC, anlage_am_um DESC, create_date DESC",
        #                          limit=1)
        lsr = self.sudo().search(domain,
                                 order="anlage_am_um DESC, create_date DESC",
                                 limit=1)

        # Return the empty record set if no lsr was found
        if not lsr:
            return lsr

        # Check that submission_id and submission_id_datetime are set for non imported donation reports
        if not lsr.imported:
            if not lsr.submission_id or not lsr.submission_id_datetime:
                raise ValidationError(_("Non imported and submitted donation report (ID %s) is not linked to a valid"
                                        "donation report submission!") % lsr.id)

        # Return the lsr also on an ERR-U-008
        # ATTENTION: ERR-U-008 error means that there was already an 'Erstmeldung' for this donation report
        #            e.g.: if the customer did a manual 'Spendenmeldung' in the FinanzOnline Website
        if lsr.state == 'response_nok' and 'ERR-U-008' in (lsr.response_error_code or ''):
            return lsr

        # Return the lsr also on an ERR-U-006 AND ERR-007
        # ATTENTION: ERR-U-006/7 error means that the lsr was an "Aenderungsmeldung" but that there was no previous
        #            donation report with for the RefNr (submission_refnr) of the Aenderungsmeldung
        #            (or the ZR or Env changed). This may only happen if donation reports where submitted by other
        #            systems or we have a bug so that we calculated RefNr of the Aenderungsmeldung instead of taking
        #            it from the former lsr.
        # HINT: This may also happen on cancellation reports if a donation report is missing in FinanzOnline
        if lsr.state == 'response_nok' and any(
                ecode in (lsr.response_error_code or '') for ecode in ('ERR-U-006', 'ERR-U-007')):
            return lsr

        # ATTENTION: If the state is 'submitted' or 'unexpected_response' we do not know if the lsr donation report
        #            was accepted by FinanzOnline or not! Therefore we throw an exception!
        if lsr.state != "response_ok":
            raise ValidationError(_("Submitted donation report (ID %s) is in state '%s' but should be "
                                    "in state 'response_ok'.") % (lsr.id, lsr.state))

        # An lsr was found with state 'response_ok'
        return lsr

    @api.multi
    def _compute_refnr(self, submission_bpk_private=False):
        """
        Computes the RefNr

        :return: str()
        """
        assert self.ensure_one(), _("_compute_refnr() works only for one record at a time!")
        assert submission_bpk_private, _("_compute_refnr() submission_bpk_private is not given!")

        # MD5-hash the private bpk
        bpk_md5 = hashlib.md5(submission_bpk_private).hexdigest()[:7]
        assert len(bpk_md5) <= 7, _("_compute_refnr() bpk_md5 hash must have 7 or less characters")

        # Get all values for the RefNr
        values = [self.meldungs_jahr, self.bpk_company_id.fa_dr_type, self.partner_id.id, bpk_md5]
        assert all(values), _("Can not compute submission_refnr because fields are missing!\n"
                              "meldungs_jahr: %s,\nbpk_company_id.fa_dr_type: %s,\npartner_id.id: %s,\n"
                              "bpk.bpk_private md5 hashed: %s") % tuple(values)

        # Return the RefNr
        refnr = "%s%s%s-%s" % tuple(values)
        assert len(refnr) <= 23, _("_compute_refnr() RefNr %s must have 23 or less charachters!") % refnr
        return refnr

    @api.multi
    def compute_type_refnr_and_links(self, submission_bpk_private=False):
        """
        Returns a dictionary with
            - submission_type,
            - submission_refnr
            - report_erstmeldung_id
            - cancelled_lsr_id

        :return: dict()
        """
        assert self.ensure_one(), _("compute_type_refnr_and_links() works only for one record at a time!")
        r = self

        # Stornierungsmeldung S
        # ---------------------
        if r.betrag <= 0:
            if not r.cancellation_for_bpk_private:
                raise ValidationError(_("cancellation_for_bpk_private must be set for a cancellation donation report!"
                                        " (ID %s)!") % r.id)

            # Search for the last submitted donation report for this cancellation PrivateBPK
            lsr = r.last_submitted_report(submission_bpk_private=r.cancellation_for_bpk_private)

            if not lsr:
                raise ValidationError(_("No successfully submitted donation reports (in state response_ok) found for "
                                        " this cancellation donation report (ID %s)!") % r.id)

            if lsr.cancellation_for_bpk_private:
                raise ValidationError(_("Last submitted report (ID %s) is already a cancellation donation report!"
                                        "There should to be no reason to cancel it again (ID %s)!") % (lsr.id, r.id))

            if lsr.submission_type != 'E' and not lsr.report_erstmeldung_id:
                raise ValidationError(_("Last submitted report (ID %s) Is not an 'Erstmelung' and has no linked "
                                        "'Erstmelung'!") % lsr.id)

            if not lsr.submission_refnr:
                raise ValidationError(_("Last submitted report (ID %s) has no RefNr!") % lsr.id)

            if lsr.submission_type != 'E' and lsr.response_error_code not in ('ERR-U-008', 'ERR-U-006', 'ERR-U-007') \
                    and (lsr.submission_refnr != lsr.report_erstmeldung_id.submission_refnr):
                raise ValidationError(_("Last submitted report (ID %s) has a different RefNr %s than it's linked"
                                        "'Erstmelung' (ID %s) Refnr %s"
                                        "!") % (lsr.id,
                                                lsr.submission_refnr,
                                                lsr.report_erstmeldung_id.id,
                                                lsr.report_erstmeldung_id.submission_refnr))

            # Cancellation donation report for ERR-U-008
            if lsr.state == 'response_nok' and 'ERR-U-008' in lsr.response_error_code or '':
                if not lsr.response_error_orig_refnr:
                    raise ValidationError(_("Last submitted report (ID %s) is an Erstmeldung with ERR-U-008 but"
                                            "the field 'response_error_orig_refnr' is empty! (donation report id %s)"
                                            "") % (lsr.id, r.id))
                return {
                    'submission_type': 'S',
                    'submission_refnr': lsr.response_error_orig_refnr,
                    'report_erstmeldung_id': lsr.report_erstmeldung_id.id if lsr.submission_type != 'E' else lsr.id,
                    'cancelled_lsr_id': lsr.id
                }

            # Cancellation donation report for ERR-U-006 and ERR-U-007
            if lsr.state == 'response_nok' and any(ecode in (lsr.response_error_code or '')
                                                   for ecode in ('ERR-U-006', 'ERR-U-007')):
                if not lsr.report_erstmeldung_id or not lsr.report_erstmeldung_id.submission_refnr:
                    raise ValidationError(_("Last submitted report (ID %s) is an ERR-U-006 or ERR-U-007 but has no "
                                            "linked Erstmeldung or the Erstmeldung has no RefNr! "
                                            "(donation report id %s)") % (lsr.id, r.id))
                return {
                    'submission_type': 'S',
                    'submission_refnr': lsr.report_erstmeldung_id.submission_refnr,
                    'report_erstmeldung_id': lsr.report_erstmeldung_id.id if lsr.submission_type != 'E' else lsr.id,
                    'cancelled_lsr_id': lsr.id
                }

            # Normal cancellation donation report
            return {
                'submission_type': 'S',
                'submission_refnr': lsr.submission_refnr,
                'report_erstmeldung_id': lsr.report_erstmeldung_id.id if lsr.submission_type != 'E' else lsr.id,
                'cancelled_lsr_id': lsr.id
            }

        # For non cancellation donation reports cancellation_for_bpk_private must be empty
        if r.cancellation_for_bpk_private and r.betrag != 0:
            raise ValidationError(_("compute_type_refnr_and_links() cancellation_for_bpk_private is set but "
                                    "betrag is not 0!"))

        # For the computation of an Erstmeldung or Aenderungsmeldung the submission_bpk_private must be known!
        if not submission_bpk_private:
            raise ValidationError(_("compute_type_refnr_and_links() submission_bpk_private not given!"))

        # Get the last submitted donation report (lsr) for this bpk
        # ---------------------------------------------------------
        lsr = r.last_submitted_report(submission_bpk_private=submission_bpk_private)

        # Erstmeldung E
        # -------------
        if not lsr:
            # Since we found no last submitted report for this bpk this must be an 'Erstmeldung'
            return {
                'submission_type': 'E',
                'submission_refnr': r._compute_refnr(submission_bpk_private=submission_bpk_private),
                'report_erstmeldung_id': False,
                'cancelled_lsr_id': False
            }

        # Erstmeldung E: if the lsr for this BPK was a cancellation donation report
        # -------------------------------------------------------------------------
        # After a cancellation an 'Erstmeldung' must be send.
        if lsr and lsr.betrag == 0 and lsr.cancellation_for_bpk_private:
            return {
                'submission_type': 'E',
                'submission_refnr': r._compute_refnr(submission_bpk_private=submission_bpk_private),
                'report_erstmeldung_id': False,
                'cancelled_lsr_id': False
            }

        # Erstmeldung E: if lsr for this BPK was error ERR-U-006 OR ERR-U-007
        # --------------------------------------------------------------------
        # Catch special case last submitted report was rejected with 'ERR-U-006' or 'ERR-U-007'
        # This error means that no Donation Report with this RefNr was found in FinanzOnline either because
        # FinanzOnline messed it up or we had a Problem:
        # HINT: It makes no sence to create a cancellation report after an error 006 or 007 because we still do not
        #       know the refnr. of any possible existing donation report in FinanzOnline. This is only given after
        #       an Erstmeldung when we get an ERR-U-008 as an response in the error text of FinanzOnline.
        # ATTENTION: This may happen if the FinanzOnline 'Steuernummer' of the org. is changed.
        if lsr and lsr.state == 'response_nok' and any(
                ecode in (lsr.response_error_code or '') for ecode in ('ERR-U-006', 'ERR-U-007')):
            # ATTENTION: Create an Erstmeldung instead of an Aenderungsmeldung! Either to get the original RefNr. by
            #            the response of ERR-U-008 or because an Erstmeldung is allowed after a 'Stornierungsmeldung'!
            return {
                'submission_type': 'E',
                'submission_refnr': r._compute_refnr(submission_bpk_private=submission_bpk_private),
                'report_erstmeldung_id': False,
                'cancelled_lsr_id': False
            }

        # Erstmeldung E: if lsr for this BPK was error ERR-U-008
        # ------------------------------------------------------
        # If the last submitted report for this submission_bpk_private had an ERR-U-008 there should
        # already exist a cancellation donation report for the 'response_error_orig_refnr' of the ERR-U-008 .
        # donation report!
        # ATTENTION: This may happen if the organisation manually submitted donation reports via the FinanzOnline
        #            webpage (or if any other unknown source submitted donation reports).
        if lsr and lsr.state == 'response_nok' and 'ERR-U-008' in lsr.response_error_code or '':
            # If the last submitted report for this submission_bpk_private had an ERR-U-008 there should
            # already exist a cancellation donation report for the 'response_error_orig_refnr' of the ERR-U-008 .
            # donation report!
            #
            # TODO: Maybe we need to wait until we can send the 'new' Erstmeldung and should set it to 'error'
            # TODO: first? (This is only needed if the same RefNr. is used for the cancellation and the new regular
            # TODO: donation report, which is unlikely because RefNr. must be unique in one submission)
            #
            return {
                'submission_type': 'E',
                'submission_refnr': r._compute_refnr(submission_bpk_private=submission_bpk_private),
                'report_erstmeldung_id': False,
                'cancelled_lsr_id': False
            }

        # Aenderungsmeldung A
        # -------------------
        # If there is a lsr for this BPK this donation report would be an 'Aenderungsmeldung'
        if lsr:

            # Check if the state of the lsr is 'response_ok' (other special cases are handled already)
            if lsr.state != 'response_ok':
                raise ValidationError(_("State of the last submitted report (ID %s) for this BPK is %s but should be "
                                        "'response_ok'! Therefore the submission_type could not be computed for this "
                                        "donation report (ID %s)") % (lsr.id, lsr.state, r.id))
            # Check that the lsr is an 'Erstmeldung' or has a linked 'Erstmeldung'
            assert lsr.submission_type == 'E' or lsr.report_erstmeldung_id, _(
                "The last submitted report (ID %s) for this report (ID %s) is not an 'Erstmeldung' and has no linked "
                "'Erstmeldung'!") % (lsr.id, r.id)

            # Check if the RefNr. changed
            # HINT: If only the partner.id changed but the the rest is the same it must have been a partner merge
            #       in this case it is ok to use the 'Erstmeldung' Refnr.
            erstm_refnr = lsr.submission_refnr
            test_refnr = r._compute_refnr(submission_bpk_private=submission_bpk_private)
            if erstm_refnr != test_refnr:
                ref_mismatch_msg = _("The computed Test-RefNr '%s' (ID %s) and the RefNr '%s' of the last submitted "
                                     "report (ID %s) do not match! Maybe company 'Submission Type' or the BPK has "
                                     "changed? The partner id was NOT checked to allow partner merging!"
                                     "") % (test_refnr, r.id, erstm_refnr, lsr.id)
                logger.warning(ref_mismatch_msg)

                # Check if Meldejahr, CompanyType and Private BPK are still the same
                if (
                        (r.meldungs_jahr != lsr.meldungs_jahr) or
                        (not lsr.imported and r.bpk_company_id.fa_dr_type != lsr.submission_id.submission_fa_dr_type) or
                        (submission_bpk_private != lsr.submission_bpk_private)
                ):
                    raise ValidationError(ref_mismatch_msg)

            # ATTENTION: We use the submission_refnr from the last submitted report in case the partner id
            #            changed after a partner merge.
            return {
                'submission_type': 'A',
                'submission_refnr': lsr.submission_refnr,
                'report_erstmeldung_id': lsr.id if lsr.submission_type == 'E' else lsr.report_erstmeldung_id.id,
                'cancelled_lsr_id': False
            }

        # If we came to this far something went awfully wrong!
        raise ValidationError("This point should never be reached while computing the submission_type!")

    @api.multi
    def update_state_and_submission_information(self):

        # Helper method to clear the correct fields of the report by state
        def update_report(report, **f):
            assert 'state' in f, "update_state_and_submission_information(): 'state' must be in fields!"
            # Clear submission fields
            if f['state'] in ('disabled', 'error', 'skipped'):
                f.update({'submission_id': False,
                          'submission_type': False,
                          'submission_refnr': False,
                          'report_erstmeldung_id': False,
                          #
                          'submission_firstname': False,
                          'submission_lastname': False,
                          'submission_birthdate_web': False,
                          'submission_zip': False,
                          #
                          'submission_bpk_request_id': False,
                          'submission_bpk_public': False,
                          'submission_bpk_private': False,
                          # Additional Info
                          'submission_bpk_state': False,
                          'submission_dd_disabled': False,
                          'submission_dd_optout': False,
                          #
                          'submission_bpk_request_date': False,
                          })
            # Clear error fields
            if f['state'] != 'error':
                f.update({'error_type': False,
                          'error_code': False,
                          'error_detail': False,
                          })
            # Clear skipped by
            if f['state'] != 'skipped':
                f.update({'skipped_by_id': False})

            # Update the report if anything changed and return
            # HINT: '... or False' is for comparison of empty records sets and alike !
            if any((report[f_name] or False) != (f[f_name] or False) for f_name in f):
                report.write(f)
            return

        # Loop through the donation reports
        logger.info("update_state_and_submission_information() "
                    "Compute state and submission information for %s donation reports!" % len(self))
        for r in self:
            # Skip donor instruction donation reports!
            # ----------------------------------------
            if r.donor_instruction:
                continue

            # Skip imported donation reports!
            # -------------------------------
            if r.imported:
                continue

            # Skip older unsubmitted reports
            # ------------------------------
            # Search for unsubmitted donation reports that are created before this report
            # HINT: Cancellation report will only skipp cancellation reports and regular reports only reg. reports
            reports_to_skip = r.sudo().search([('donor_instruction', '=', False),
                                               ('submission_env', '=', r.submission_env),
                                               ('partner_id', '=', r.partner_id.id),
                                               ('bpk_company_id', '=', r.bpk_company_id.id),
                                               ('meldungs_jahr', '=', r.meldungs_jahr),
                                               ('cancellation_for_bpk_private', '=', r.cancellation_for_bpk_private),
                                               ('state', 'in', r._changes_allowed_states()),
                                               ('anlage_am_um', '<', r.anlage_am_um),
                                               ('id', '!=', r.id)])
            # Skip older reports and unlink them from any donation_report.submission
            # HINT: We are already the superuser in this environment
            for report_to_skip in reports_to_skip:
                update_report(report_to_skip, state='skipped', skipped_by_id=r.id)

            # Search for other reports with the same anlage_am_um date
            # --------------------------------------------------------
            # HINT: This may only happen after a merge of two partners because anlage_am_um is checked in create()
            reports_same_date = r.sudo().search([('donor_instruction', '=', False),
                                                 ('submission_env', '=', r.submission_env),
                                                 ('partner_id', '=', r.partner_id.id),
                                                 ('bpk_company_id', '=', r.bpk_company_id.id),
                                                 ('meldungs_jahr', '=', r.meldungs_jahr),
                                                 ('cancellation_for_bpk_private', '=', r.cancellation_for_bpk_private),
                                                 ('state', 'in', r._changes_allowed_states()),
                                                 ('anlage_am_um', '=', r.anlage_am_um),
                                                 ('id', '!=', r.id)])
            if reports_same_date:
                msg = _("update_state_and_submission_information() Report(s) (%s) with same anlage_am_um as "
                        "this report (ID %s) found! Maybe there was a partner merge? Skipping all unsubmitted reports "
                        "because a new donation report total is expected for the partner %s (ID %s)! "
                        "" % (reports_same_date.ids, r.id, r.partner_id.name, r.partner_id.id))
                logger.warning(msg)
                msg = (r.info or '') + msg
                logger.info("update_state_and_submission_information() Skipp other reports with same anlage_am_um "
                            "date (IDS %s)" % reports_same_date.ids)
                for report_same_date in reports_same_date:
                    update_report(report_same_date, state='skipped', skipped_by_id=r.id, info=msg)
                if r.state in self._changes_allowed_states():
                    logger.info("update_state_and_submission_information() Skipp report (ID %s) because other reports "
                                "with the same anlage_am_um date where found!" % r.id)
                    update_report(r, state='skipped', skipped_by_id=False, info=msg)
                continue

            # Avoid any changes to this report if it was skipped or submitted!
            # ----------------------------------------------------------------
            if r.state and r.state not in self._changes_allowed_states():
                logger.error("update_state_and_submission_information() Will not recompute state and vals because "
                             "donation report state is %s for donation report (ID %s)" % (r.state, r.id))
                continue

            # Skip this report if newer reports exists already because of sosync LIFO!
            # ------------------------------------------------------------------------
            # HINT: It was already checked above that this report is in a state where changes are allowed.
            # HINT: Only newer cancellation reports (with matching PrivateBPK) can skipp a cancellation report and
            #       only newer regular reports can skip a regular report
            newer = r.sudo().search([('donor_instruction', '=', False),
                                     ('submission_env', '=', r.submission_env),
                                     ('partner_id', '=', r.partner_id.id),
                                     ('bpk_company_id', '=', r.bpk_company_id.id),
                                     ('meldungs_jahr', '=', r.meldungs_jahr),
                                     ('cancellation_for_bpk_private', '=', r.cancellation_for_bpk_private),
                                     ('anlage_am_um', '>', r.anlage_am_um),
                                     ('id', '!=', r.id)],
                                    order="anlage_am_um DESC", limit=1)
            if newer:
                update_report(r, state='skipped', skipped_by_id=newer.id)
                continue

            # Skip this report if the betrag is 0 and cancellation_for_bpk_private is NOT set!
            # --------------------------------------------------------------------------------
            # HINT: This should only happen if in FRST regular donation exists but none of them seems to be submitted
            #       and the betrag went down to 0 or donation deduction was disabled!
            #       If the regular donation reports where already submitted but the state was just not synced to FRST
            #       this report will go into error state and will never be submitted (which is correct)
            if r.betrag == 0 and not r.cancellation_for_bpk_private:
                try:
                    # Check if there is a last submitted donation report with a betrag greater than 0
                    lsr = r.last_submitted_report()
                    if lsr and lsr.betrag > 0:
                        update_report(r, state='error', error_type='zero_but_lsr', error_code=False,
                                      error_detail="Donations are already submitted! Therefore you must use a "
                                                   "cancellation donation report (with cancellation_for_bpk_private "
                                                   "set)! Maybe the state was not synced?")
                        continue
                    else:
                        # HINT: All other reports should already be skipped at this point!
                        update_report(r, state='skipped', skipped_by_id=False,
                                      info="Can be skipped because there are no submitted reports or the "
                                           "last submitted 'betrag' is already 0")
                        continue
                except Exception as e:
                    update_report(r, state='error', error_type='zero_lsr_exception', error_code=False,
                                  error_detail="Exception while searching for the last submitted report!\n%s" % repr(e))
                    continue

            # Check Donation Deduction Disabled for this partner
            # --------------------------------------------------
            # HINT: Exclude cancellation donation reports because they always needs to be send!
            # ATTENTION: Honor individual donor instructions
            if not r.cancellation_for_bpk_private:

                # Check for any last donor instruction
                last_instruction = r.sudo().search([('donor_instruction', '!=', False),
                                                    ('submission_env', '=', r.submission_env),
                                                    ('partner_id', '=', r.partner_id.id),
                                                    ('bpk_company_id', '=', r.bpk_company_id.id),
                                                    ('meldungs_jahr', '=', r.meldungs_jahr),
                                                    ('id', '!=', r.id)],
                                                   order="anlage_am_um DESC", limit=1)

                # Last donor instruction is to forbid any submission for this year and org
                if last_instruction and last_instruction.donor_instruction == 'submission_forbidden':
                    update_report(r, state='disabled')
                    continue

                # There is no specific donor instruction or it is at least not 'submission_forced'
                # In this case we check the global settings of the partner (donation deduction groups settings)
                if not last_instruction or last_instruction.donor_instruction != 'submission_forced':
                    if (r.partner_id.bpk_state == 'disabled'
                            or r.partner_id.donation_deduction_optout_web
                            or r.partner_id.donation_deduction_disabled):
                        update_report(r, state='disabled')
                        continue

            # Check BPK request pending for this partner
            # ------------------------------------------
            # HINT: Exclude cancellation donation reports
            if not r.cancellation_for_bpk_private and r.partner_id.bpk_state == 'pending':
                update_report(r, state='error', error_type='bpk_pending', error_code=False, error_detail=False)
                continue

            # Search for a related bpk record
            bpk = r._get_bpk()

            # Check BPK not found
            # -------------------
            # HINT: Exclude cancellation donation reports
            if not r.cancellation_for_bpk_private and (not bpk or (bpk and bpk.state != 'found')):
                update_report(r, state='error', error_type='bpk_missing', error_code=False, error_detail=False)
                continue

            # Check if there are any donation reports for this private BPK but for a different partner
            # ----------------------------------------------------------------------------------------
            # ATTENTION: Such partners must be merged before the donation report can be submitted
            # HINT: It is ok if there are donation reports for the same partner with different bpk numbers
            # HINT: If is ok if there are other partners with the same BPK but no donation reports
            # ATTENTION: This test can !!!NOT!!! be applied to cancellation donation reports!
            bpk_private = bpk.bpk_private
            if bpk_private and (not r.cancellation_for_bpk_private and r.betrag > 0):

                # Search for non-cancellation donation reports with a different partner but the same private BPK number
                r_same_bpk = r.sudo().search(
                    [('partner_id', '!=', r.partner_id.id),
                     ('bpk_company_id', '=', r.bpk_company_id.id),
                     ('betrag', '>', 0),
                     ('submission_bpk_private', '=', bpk_private)])

                # If the last donation report of the "other" person is a successfully submitted
                # "Stornierungsmeldung" and the private BPK of the 'other' person is no longer the private BPK of 'this'
                #  person the reports of the other person do not belong into r_same_bpk and will be removed from the set
                if r_same_bpk:
                    partners_with_same_bpk_reports = r_same_bpk.mapped('partner_id')
                    assert partners_with_same_bpk_reports, "Programming Error! partners_with_same_bpk_reports is empty!"

                    # Loop through the partners and check if the donation reports are still to consider
                    for p in partners_with_same_bpk_reports:

                        # Get the donation reports in r_same_bpk for this partner
                        p_dr = r_same_bpk.filtered(lambda rep: rep.partner_id == p)
                        assert p_dr, "Programming Error! There must be donation reports in r_same_bpk for this partner!"

                        # Only check if we can remove records from r_same_bpk if this partner has already a different
                        # private BPK or no valid BPK at all
                        if p.bpk_state in ('new', 'found', 'pending'):
                            # HINT: _get_bpk() will update the BPK for the partner if 'new' or 'pending'
                            p_bpk_record = p_dr[0]._get_bpk()
                            p_bpk_private = p_bpk_record.bpk_private
                            if p_bpk_private == bpk_private:
                                # Since the BPK was neither disabled nor changed we can not remove the p_dr and
                                # continue with the next partner
                                continue

                        # Remove the donation reports from r_same_bpk if the last donation report is a successfully
                        # submitted cancellation report
                        # HINT: sorted() will always return the lowest first (except reverse=True is given)
                        #p_dr = p_dr.sorted(key=lambda rep: rep.anlage_am_um, reverse=True)
                        #p_last_dr = p_dr[0]
                        try:
                            p_last_dr = p_dr[0].last_submitted_report(submission_bpk_private=bpk_private)
                        except Exception as e:
                            logger.warning('update_state_and_submission_information() p_last_dr: %s' % repr(e))
                            p_last_dr = False
                            pass
                        if p_last_dr and p_last_dr.state == 'response_ok' and p_last_dr.submission_type == 'S':
                            r_same_bpk = r_same_bpk - p_dr

                # If there are still reports set this and the other donation reports to state 'error'
                if r_same_bpk:
                    # Create an error message
                    error_detail = _("Reports found with the same private BPK but a different Partner!\nInvolved "
                                     "reports:\n%s") % "\n".join("Report ID: "+str(rep.id) for rep in (r | r_same_bpk))
                    # Update this report
                    update_report(r, state='error', error_type='bpk_not_unique', error_code=False,
                                  error_detail=error_detail)
                    # Update other reports if possible
                    for report_same_bpk in r_same_bpk:
                        if report_same_bpk.state in self._changes_allowed_states():
                            update_report(report_same_bpk, state='error', error_type='bpk_not_unique', error_code=False,
                                          error_detail=error_detail)
                    continue

            # Compute the submission values
            # -----------------------------
            # HINT: If no 'valid' bpk request was found or a bpk request is needed or donation deduction is disabled
            #       we would never have reached this point!
            # ATTENTION: The submission_bpk_private is mandatory for the computation of the 'submission_type',
            #            the 'submission_refnr' and the 'report_erstmeldung_id'
            subm_vals = {
                'submission_bpk_private': r.cancellation_for_bpk_private or bpk.bpk_private,
                #
                'submission_bpk_request_id': False if r.cancellation_for_bpk_private else bpk.id,
                'submission_bpk_public': False if r.cancellation_for_bpk_private else bpk.bpk_public,
                #
                'submission_firstname': False if r.cancellation_for_bpk_private else bpk.bpk_request_firstname,
                'submission_lastname': False if r.cancellation_for_bpk_private else bpk.bpk_request_lastname,
                'submission_birthdate_web': False if r.cancellation_for_bpk_private else bpk.bpk_request_birthdate,
                'submission_zip': False if r.cancellation_for_bpk_private else bpk.bpk_request_zip,
                # Add additional Info
                'submission_bpk_state': False if r.cancellation_for_bpk_private else r.partner_id.bpk_state,
                'submission_dd_disabled': False if r.cancellation_for_bpk_private else r.partner_id.donation_deduction_disabled,
                'submission_dd_optout': False if r.cancellation_for_bpk_private else r.partner_id.donation_deduction_optout_web,
                #
                'submission_bpk_request_date': False if r.cancellation_for_bpk_private else bpk.bpk_request_date,
            }
            try:
                # Compute: 'submission_type', 'submission_refnr', 'report_erstmeldung_id' and 'cancelled_lsr_id'
                type_refnr_erstmid = r.compute_type_refnr_and_links(
                    submission_bpk_private=subm_vals['submission_bpk_private'])

                # Add these fields to the subm_vals
                subm_vals.update(type_refnr_erstmid)

            except Exception as e:
                update_report(r, state='error', error_type='data_incomplete', error_code='exception',
                              error_detail=repr(e))
                continue

            # Check if all needed values are available
            # ----------------------------------------
            if r.betrag <= 0:
                # HINT: submission_bpk_private == cancellation_for_bpk_private for cancellation donation reports
                #       check the subm_vals above
                mandatory_submission_fields = ('submission_type', 'submission_refnr', 'submission_bpk_private')
            else:
                mandatory_submission_fields = ('submission_type',
                                               'submission_refnr',
                                               'submission_firstname',
                                               'submission_lastname',
                                               'submission_birthdate_web',
                                               'submission_bpk_request_id',
                                               'submission_bpk_public',
                                               'submission_bpk_private')
            missing_fields = [field for field in mandatory_submission_fields if not subm_vals[field]]
            if missing_fields:
                error_detail = 'Missing Donation-Report submission fields: %s' % ";".join(f for f in missing_fields)
                logger.error(error_detail)
                update_report(r, state='error', error_type='data_incomplete', error_code=False,
                              error_detail=error_detail)
                continue

            # Update the donation report
            # --------------------------
            subm_vals.update({'state': 'new',
                              'skipped_by_id': False,
                              'submission_id': r.submission_id.id if r.submission_id else False,
                              'error_type': False,
                              'error_code': False,
                              'error_detail': False})
            # Update the report if anything changed
            # HINT: hasattr(r[f_name], 'id') is to check correctly many2one fields
            if any(r[f_name].id != subm_vals[f_name] if hasattr(r[f_name], 'id') else r[f_name] != subm_vals[f_name]
                   for f_name in subm_vals):
                r.write(subm_vals)
            continue

    @api.multi
    def manual_force_skipp(self):
        assert self.ensure_one(), _("manual_force_skipp() works only for one record at a time!")
        assert self.env.user.id == SUPERUSER_ID, _("manual_force_skipp() must be run by user admin!")

        if self:
            assert self.state in self._changes_allowed_states(), _("Force skipp not allowed in state %s") % self.state
            self.write({
                'state': 'skipped',
                'info':  '!!! Manually force skipped !!!\n' + (self.info or ''),
                'submission_id': False,
                'submission_type': False,
                'submission_refnr': False,
                'report_erstmeldung_id': False,
                'skipped_by_id': False,
                'cancelled_lsr_id': False,
                #
                'submission_firstname': False,
                'submission_lastname': False,
                'submission_birthdate_web': False,
                'submission_zip': False,
                #
                'submission_bpk_request_id': False,
                'submission_bpk_public': False,
                'submission_bpk_private': False,
                #
                'submission_bpk_request_date': False,
                #
                'error_type': False,
                'error_code': False,
                'error_detail': False,
            })

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
        if res:
            res.update_state_and_submission_information()

        # Return the record (create it in db)
        return res

    @api.multi
    def write(self, vals):

        for r in self:

            # Only run these checks for non imported donation reports
            imported = vals.get('imported') if 'imported' in vals else r.imported
            if not imported:

                # Prevent an FinanzOnline environment change after the donation report got created.
                if vals and 'submission_env' in vals and vals['submission_env'] != r.submission_env:
                    raise ValidationError(_("You can not change the environment once the donation report got created!"))

                # Prevent any changes to the basic fields after submission
                # HINT: Changes must be also allowed in the response_nok state for report release button
                changes_allowed_states = list(self._changes_allowed_states())
                changes_allowed_states.append('response_nok')
                if r.state and r.state not in changes_allowed_states:
                    changes_allowed_fields = self._changes_allowed_fields_after_submission()
                    if any((vals[field] or False) != (r[field] or False) for field in vals
                           if field not in changes_allowed_fields):
                        raise ValidationError(_("Changes to some of the fields in %s are only allowed in the states "
                                                "%s!") % (vals, str(self._changes_allowed_states())))

        # ATTENTION: After this 'self' is changed in memory and 'res' is only a boolean !
        res = super(ResPartnerFADonationReport, self).write(vals)

        # Compute the state
        # HINT: Will also compute and write the submission values if in unsubmitted states
        if res and (not vals or 'state' not in vals or not vals['state']):
            if not vals.get('submission_id', False):
                self.update_state_and_submission_information()

        # Return the recordset
        return res

    @api.multi
    def unlink(self):
        states_allowed = list(self._changes_allowed_states()) + ['skipped']
        for r in self:
            # TODO: Check what happens on partner merge and update remaining donation reports with the
            #       so that the state may switch from error>bpk_no_unique to new

            # Make sure only test donation reports in the correct states can be deleted!
            # TODO: This may be a problem on partner merges test it!
            if r.submission_env not in ['t', 'T'] or r.state not in states_allowed:
                raise ValidationError(_("Deletion only allowed for test donation reports in the states"
                                        " %s") % states_allowed)

        return super(ResPartnerFADonationReport, self).unlink()

    # ------------------------------------------
    # SCHEDULER ACTIONS FOR AUTOMATED PROCESSING
    # ------------------------------------------
    @api.model
    def scheduled_set_donation_report_state(self):
        logger.info(_("scheduled_set_donation_report_state(): START"))
        now = time.time

        while_start = now()

        # Do it for all donation reports in the correct states
        donation_reports_to_check_ids = self.search([('state', 'in', self._changes_allowed_states())]).ids

        # Log info about the search
        total_to_check = len(donation_reports_to_check_ids)
        logger.info(_("scheduled_set_donation_report_state(): Found a total of %s donation reports to "
                      "check in %.6f seconds") % (total_to_check, now() - while_start))

        # Start batch processing
        report_batch = True
        batch_size = 1000
        offset = 0
        while report_batch:
            start = now()

            # Do every batch in its own environment and therefore in an isolated db-transaction
            # HINT: This reduces the RAM and saves all "in between" results if the process should crash
            # You don't need clear caches because they are cleared when "with" finishes
            with openerp.api.Environment.manage():

                # You don't need close your cr because is closed when finish "with"
                with openerp.registry(self.env.cr.dbname).cursor() as new_cr:

                    # Create a new environment with new cursor database
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                    # HINT: 'with_env' replaces original env for this method
                    #       This forces an isolated transaction to commit
                    report_batch = self.with_env(new_env).browse(
                        donation_reports_to_check_ids[offset:offset + batch_size])

                    # Increase offset for next batch
                    offset += batch_size

                    # Compute the state and submission values for the found donation reports
                    found_reports = report_batch
                    count = len(found_reports)
                    found_reports.update_state_and_submission_information()

                    # Commit the changes in the new environment
                    new_env.cr.commit()  # Don't show a invalid-commit in this case

                    # Log some info for this batch run
                    duration = now() - start
                    tpr = 0 if not count or not duration else duration / count
                    logger.debug(_("scheduled_set_donation_report_state(): "
                                   "Set update_state_and_submission_information() "
                                   "done for %s donation reports in %.3f seconds (%.3fs/p)"
                                   "") % (count, duration, tpr))

            # Log estimated remaining time
            reports_done = offset - batch_size + len(report_batch)
            total_duration = now() - while_start
            time_per_record = 0 if not reports_done else total_duration / reports_done
            remaining_reports = total_to_check - reports_done
            time_left = remaining_reports * time_per_record
            logger.info(_("scheduled_set_donation_report_state(): "
                          "PROCESSED A TOTAL OF %s DONATION REPORTS IN %.3f SECONDS (%.3fs/p)! "
                          "%s DONATION REPORTS PENDING (approx %.2f minutes left)"
                          "") % (reports_done, total_duration, time_per_record, remaining_reports, time_left / 60))

        logger.info(_("scheduled_set_donation_report_state(): END"))

    @api.model
    def cron_compute_donation_report_state(self):
        """
        This will set the state computation cron nextcall date to now
        :return: boolean
        """
        action = self.env.ref('fso_con_zmr.ir_cron_scheduled_set_donation_report_state')
        if action:
            try:
                # HINT: The related cron job is in data.xml
                # HINT: The cron job will run scheduled_set_donation_report_state()
                # now = fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                now = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                action.write({'active': True, 'nextcall': now})
            except Exception as e:
                logger.error("Could not set execution date of ir_cron.ir_cron_scheduled_set_donation_report_state to "
                             "now! \n%s" % repr(e))
