# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError
from openerp.addons.fso_base.tools.soap import render_template, soap_request
from openerp.addons.fso_base.tools.email_tools import send_internal_email
from openerp.addons.fso_base.tools.server_tools import is_production_server
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

import base64
import datetime
from lxml import etree
import re
import os
from os.path import join as pj
import time
import pprint
import logging
pp = pprint.PrettyPrinter(indent=2)
logger = logging.getLogger(__name__)


class ResPartnerFADonationReport(models.Model):
    _name = 'res.partner.donation_report.submission'
    _inherit = ['mail.thread']
    #_rec_name = 'name'
    _order = 'submission_datetime DESC'

    now = fields.datetime.now

    # ------
    # FIELDS
    # ------
    name = fields.Char(string="Name", compute="compute_name", readonly=True,
                       compute_sudo=True, store=False)

    state = fields.Selection(string="State", readonly=True, default='new', track_visibility='onchange',
                             selection=[('new', 'New'),
                                        ('prepared', 'Prepared'),
                                        ('error', 'Error'),
                                        ('submitted', 'Submitted to FinanzOnline'),
                                        ('response_ok', 'Accepted by FinanzOnline'),
                                        ('response_nok', 'Rejected by FinanzOnline'),
                                        ('response_twok', 'Partially Rejected by FinanzOnline'),
                                        ('unexpected_response', 'Unexpected Response')],
                             index=True)

    manual = fields.Boolean(string="Manual Submission", track_visibility='onchange',
                            help="If set donation reports can only be added manually to this submission!"
                                 "The 'Prepare' button will not add new donation reports automatically to this "
                                 "submission!",
                            readonly=True, states={'new': [('readonly', False)], 'error': [('readonly', False)]})

    # Error fields for states 'error'
    # ATTENTION: The state error is only valid PRIOR to submission of for file upload service error!
    # ----------------------------------------------------------------------------------------------
    # HIN File Upload Service error means no data could be submitted so we can retry the submission later
    error_type = fields.Selection(string="Error Type", readonly=True, track_visibility='onchange',
                                  selection=[('data_incomplete', 'Data incomplete'),
                                             ('preparation_error', 'Preparation Error'),
                                             ('changes_after_prepare', 'Preparation data not up to date'),
                                             ('donation_report_limit', 'Donation report limit exceeded'),
                                             # Submission Exception (Timeout or generic exception)
                                             ('submission_exception', 'Submission Exception'),
                                             # http_error
                                             ('http_code_not_200', 'HTTP Status Code not 200'),
                                             # File Upload Service Error (return code -1 to -5)
                                             ('file_upload_error', 'FinanzOnline File Upload Error'),
                                             ('session_id', 'Session ID invalid or expired'),
                                             ('service_down_maintenance', 'Service down by maintenance'),
                                             ('technical', 'Technical Error'),
                                             ('parser', 'Parser Error'),
                                             ('file_upload_doctype', 'Upload Denied for this Document Type'),
                                             ])
    error_code = fields.Char(string="Error Code", redonly=True, track_visibility='onchange',)
    error_detail = fields.Text(string="Error Detail", readonly=True, track_visibility='onchange')

    # Company
    # -----------
    bpk_company_id = fields.Many2one(string="BPK Company", required=True, readonly=True,
                                     comodel_name='res.company',  inverse_name="donation_report_submission_ids",
                                     states={'new': [('readonly', False)]},
                                     track_visibility='onchange',
                                     index=True)

    # Submission data computed in the 'prepare' state and updated right before submission
    # -----------------------------------------------------------------------------------
    # <fileuploadRequest>
    submission_fa_tid = fields.Char(string="Teilnehmer Identifikation (tid)", readonly=True,
                                    track_visibility='onchange',)
    submission_fa_benid = fields.Char(string="Webservicebenutzer ID (benid)", readonly=True,
                                      track_visibility='onchange',)
    submission_fa_art = fields.Selection(string="Uebermitlungsbereich (art)",
                                         selection=[('UEB_SA', 'Sonderausgaben (UEB_SA)')],
                                         default="UEB_SA", readonly=True,
                                         track_visibility='onchange',)
    submission_env = fields.Selection(string="FinanzOnline Environment (uebermittlung)",
                                      default="T",
                                      selection=[('T', 'Test'), ('P', 'Production')],
                                      required=True, readonly=True, states={'new': [('readonly', False)]},
                                      track_visibility='onchange',
                                      index=True)

    # <data><SonderausgabenUebermittlung><Info_Daten>
    submission_fa_fastnr_fon_tn = fields.Char(string="Finanzamt-Steuernummer des Softwareherstellers (Fastnr_Fon_Tn)",
                                              help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus"
                                                   " dem Finanzamt (03-98) und aus der Steuernummer (7-stellig) "
                                                   "zusammen. (ohne Trennzeichen) (Fastnr_Fon_Tn)",
                                              size=9, readonly=True,
                                              track_visibility='onchange',)
    submission_fa_fastnr_org = fields.Char(string="Finanzamt-Steuernummer der Organisation (Fastnr_Org)",
                                           help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus "
                                                "dem Finanzamt (03-98) und aus der Steuernummer (7-stellig) zusammen. "
                                                "(ohne Trennzeichen) (Fastnr_Org)",
                                           size=9, readonly=True,
                                           track_visibility='onchange',)

    # <data><SonderausgabenUebermittlung><MessageSpec>
    # FORMAT: S21-123456789-20180729023009
    #         S{id}-{submission_fa_fastnr_org}-{datetime}
    submission_message_ref_id = fields.Char(string="Paket ID (MessageRefId)", readonly=True, size=36,
                                            track_visibility='onchange',
                                            index=True)
    submission_timestamp = fields.Char(string="Timestamp (Timestamp)", readonly=True,
                                       help=_("Format: datetime with timezone e.g.: 2012-12-13T12:12:12"),
                                       track_visibility='onchange',)
    submission_fa_dr_type = fields.Char(string="Organisationstyp (Uebermittlungsart)", readonly=True,
                                        track_visibility='onchange',)

    meldungs_jahr = fields.Selection(string="Year", required=True,
                                     help=_("Donation deduction year (Meldejahr)"),
                                     readonly=True, states={'new': [('readonly', False)]},
                                     selection=[(str(i), str(i)) for i in range(2017, int(now().year)+11)],
                                     track_visibility='onchange',
                                     index=True)

    # <data><SonderausgabenUebermittlung><Sonderausgaben> (for loop)
    donation_report_ids = fields.One2many(string="Donation Reports",
                                          comodel_name='res.partner.donation_report', inverse_name="submission_id",
                                          readonly=True, states={'new': [('readonly', False)]},
                                          index=True)

    # Information copied but not included in the template:
    submission_fa_herstellerid = fields.Char(string="UID-Nummer des Softwareherstellers (herstellerid)",
                                             help="Umsatzsteuer-Identifikations-Nummer (UID-Nummer) des "
                                                  "Softwareherstellers.",
                                             size=24, readonly=True,
                                             track_visibility='onchange',)

    # Content and "Submit-to-URL"
    # ---------------------------
    submission_url = fields.Char(string="Submission URL", readonly=True,
                                 default="https://finanzonline.bmf.gv.at/fon/ws/fileupload",
                                 help=_("The FinanzOnline File Upload Webservice URL (static)"))
    submission_content = fields.Text(string="Submission Content", readonly=True,
                                     help=_("The rendered template (which is the 'body' of the submission request!)"))

    submission_content_file = fields.Binary(string="Submission Content File", readonly=True,
                                            compute="compute_submission_content_file", compute_sudo=True,
                                            store=True)
    submission_content_filename = fields.Char(string="Submission Content Filename", readonly=True,
                                              compute="compute_submission_content_file", compute_sudo=True,
                                              store=True)

    # Updated at submission
    # ---------------------
    submission_datetime = fields.Datetime(string="Last submission request", readonly=True,
                                          help=_("The Date and Time of the last submission request."),
                                          index=True)
    submission_log = fields.Text(string="Submission Log", readonly=True)

    # Response (updated after submission based on the answer)
    # --------
    response_http_code = fields.Char(string="Response HTTP Code", readonly=True)
    response_content = fields.Text(string="Response Content (raw)", readonly=True)
    response_content_parsed = fields.Text(string="Response Content (prettyprint)", readonly=True)

    response_error_type = fields.Selection(string="Response Error Type", readonly=True, track_visibility='onchange',
        selection=[
                   # <Info>NOK</Info> and <Error><Code>ERR-F-*
                   ('nok', 'Donation report submission fully rejected'),
                   # <Info>TWOK</Info>
                   ('twok', 'Donation reports partially rejected'),
                   # Unexpected or no response
                   ('unexpected_no_response', 'No Response'),
                   ('unexpected_no_content', 'Response content empty or missing'),
                   ('unexpected_parser', 'Response could not be parsed'),
                   ('unexpected_exception', 'Exception during response processing'),
                   ],
                                           index=True)
    response_error_code = fields.Char(string="Response Error Code", readonly=True, track_visibility='onchange')
    response_error_detail = fields.Text(string="Response Error Detail", readonly=True, track_visibility='onchange')
    response_error_orig_refnr = fields.Char(string="Response Error Orig RefNr", readonly=True,
                                            track_visibility='onchange')

    request_duration = fields.Char(string="Request Duration (seconds)", readonly=True)

    # DataBox
    databox_listing = fields.Text(string="Databox File List", readonly=True)
    response_file_applkey = fields.Char(string="Response File FinanzOnline ID (applkey)", readonly=True,
                                        help="File Listing from FinanzOnline DataBox",
                                        track_visibility='onchange')
    response_file = fields.Text(string="Response File (raw)", readonly=True,
                                help="Response File from FinanzOnline DataBox")
    response_file_pretty = fields.Text(string="Response File (pretty)", readonly=True,
                                       help="Response File from FinanzOnline DataBox")

    # ---------------
    # COMPUTED FIELDS
    # ---------------
    @api.depends('submission_message_ref_id', 'meldungs_jahr', 'submission_env')
    def compute_name(self):
        for r in self:
            name = 'S' + str(r.id)
            try:
                if r.submission_env:
                    name += '_' + r.submission_env
                if r.meldungs_jahr:
                    name += '_' + r.meldungs_jahr
                if r.create_date:
                    name += '_' + str(r.create_date).split()[0]
            except Exception as e:
                logger.warning("Field 'name' computation of donation report submission failed: %s" % repr(e))
                pass
            r.name = name

    @api.depends('submission_content')
    def compute_submission_content_file(self):
        for r in self:
            if r.submission_content:
                try:
                    r.submission_content_file = r.submission_content.encode('utf-8', 'ignore').encode('base64')
                    r.submission_content_filename = "submission_content.xml"
                except Exception as e:
                    logger.error("Could not convert submission_content to file:\n%s" % repr(e))
                    r.submission_content_file = False
                    r.submission_content_filename = False
                    pass
            else:
                r.submission_content_file = False
                r.submission_content_filename = False

    # ----
    # CRUD
    # ----
    @api.multi
    def unlink(self):
        # Make sure no submitted submission are deleted
        for r in self:
            if r.state not in ['new', 'prepared', 'error']:
                raise ValidationError(_("Donation report submissions can not be deleted in state %s !") % r.state)

        # Delete
        return super(ResPartnerFADonationReport, self).unlink()

    # --------------
    # HELPER METHODS
    # --------------
    def file_upload_error_return_codes(self):
        fuerc = {'-1': 'session_id',
                 '-2': 'service_down_maintenance',
                 '-3': 'technical',
                 '-4': 'parser',
                 '-5': 'file_upload_doctype',
                }
        return fuerc

    def mandatory_fields(self):
        return 'submission_env', 'meldungs_jahr', 'bpk_company_id', 'submission_fa_art'

    @api.multi
    def compute_submission_values(self):
        """
        Compute the submission values!
        This will also update the state and the submission values of all found donation reports!
        :return: dict with the submission values
        """
        assert self.ensure_one(), _("compute_submission_values() can only be called for a single record!")
        r = self

        # COMPUTE THE SUBMISSION VALUES
        # -----------------------------
        logger.info("compute_submission_values() START")

        # Search for donation reports to submit
        # -------------------------------------
        # ATTENTION: It is very important to sort the donation reports by anlage_am_um descending so that cancellation
        #            donation reports are before regular reports in the xml file.
        # ATTENTION: A maximum of 10000 donation reports are allowed in one file!
        # HINT: This is already the _order of the res.partner.donation_report model but is added here again for savety!
        logger.info("compute_submission_values() Search for donation reports in state new that are not already "
                    "linked to any submission or are already linked to this submission.")
        if r.manual:
            # Only use donation reports that are already linked to this submission in manual mode
            donation_reports = self.env['res.partner.donation_report'].sudo().search(
                [('state', '=', 'new'),
                 ('submission_id', '=', r.id),
                 ('submission_env', '=', r.submission_env),
                 ('meldungs_jahr', '=', r.meldungs_jahr),
                 ('bpk_company_id', '=', r.bpk_company_id.id)],
                order='partner_id, anlage_am_um ASC, create_date ASC', limit=10000)
        else:
            # Use donation reports that are already linked to this report or not linked to any submission yet
            donation_reports = self.env['res.partner.donation_report'].sudo().search(
                [('state', '=', 'new'),
                 "|", ('submission_id', '=', False),
                      ('submission_id', '=', r.id),
                 ('submission_env', '=', r.submission_env),
                 ('meldungs_jahr', '=', r.meldungs_jahr),
                 ('bpk_company_id', '=', r.bpk_company_id.id)],
                order='partner_id, anlage_am_um ASC, create_date ASC', limit=10000)

        if not donation_reports:
            raise ValidationError(_("Preparation failed: No donation reports to submit found!"))

        len_dr = len(donation_reports)
        logger.info("compute_submission_values() Found %s donation reports for submission (ID %s)!" % (len_dr, r.id))

        # Compute the basic submission values
        # -----------------------------------
        # HINT: the session id is only computed and needed right before submission!
        # ATTENTION: submission_timestamp is used for the PREPARATION time of the submission values and NOT
        #            the time of the report submission try!!!
        logger.info("compute_submission_values() compute submission values!")
        vals = {
            # <fileuploadRequest>
            'submission_fa_tid': r.bpk_company_id.fa_tid,
            'submission_fa_benid': r.bpk_company_id.fa_benid,
            # <data><SonderausgabenUebermittlung><Info_Daten>
            'submission_fa_fastnr_fon_tn': r.bpk_company_id.fa_fastnr_fon_tn,
            'submission_fa_fastnr_org': r.bpk_company_id.fa_fastnr_org,
            # <data><SonderausgabenUebermittlung><MessageSpec>
            # S{id}-{submission_fa_fastnr_org}-{datetime}
            'submission_message_ref_id': "S%s-%s-%s" % (r.id,
                                                        r.bpk_company_id.fa_fastnr_org,
                                                        ''.join(re.findall(ur"(?u)[0-9]+", r.create_date))
                                                        ),
            'submission_timestamp': fields.datetime.utcnow().replace(microsecond=0).isoformat(),
            'submission_fa_dr_type': u'MÖ' if r.bpk_company_id.fa_dr_type == 'MO' else r.bpk_company_id.fa_dr_type,
            # <data><SonderausgabenUebermittlung><Sonderausgaben> (for loop)
            'donation_report_ids': [(6, 0, donation_reports.ids)],
            # Information copied but not included in the jinja2 template:
            'submission_fa_herstellerid': r.bpk_company_id.fa_herstellerid,
            # FinanzOnline File Upload Webservice URL
            'submission_url': r.submission_url,
        }

        # Render the request content template and add it to the submission vals
        # ---------------------------------------------------------------------
        logger.info("compute_submission_values() Render the submission xml template!")

        # Get the path to the template 'fo_donation_report_j2template.xml '
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        fo_donation_report_j2template = pj(soaprequest_templates, 'fo_donation_report_j2template.xml')
        assert os.path.exists(fo_donation_report_j2template), _("fo_donation_report_j2template.xml not found at "
                                                                "%s") % fo_donation_report_j2template

        # Prepare the donation reports as a list with nested dicts for the jinja2 template
        logger.info("compute_submission_values() Render the submission xml template: prepare reports as list!")
        donation_reports_list = [{'sub_typ': do_rep.submission_type,
                                  'RefNr': do_rep.submission_refnr,
                                  'Betrag': "%.2f" % do_rep.betrag,
                                  'vbPK': do_rep.submission_bpk_public} for do_rep in donation_reports]

        # Render the template for the request content (body)
        # ATTENTION: !!! '###SessionID###' will be replaced by submit() with the correct session id !!!
        #            So do not change this here!
        # HINT: Jinja expects unicode and will return unicode!
        #       https://stackoverflow.com/questions/22181944/using-utf-8-characters-in-a-jinja2-template
        logger.info("compute_submission_values() Render the submission xml template: render template!")
        content = render_template(template=fo_donation_report_j2template,
                                  submission={
                                      'tid': vals['submission_fa_tid'],
                                      'benid': vals['submission_fa_benid'],
                                      'id': '###SessionID###',
                                      'art': r.submission_fa_art,
                                      'uebermittlung': r.submission_env,
                                      'Fastnr_Fon_Tn': vals['submission_fa_fastnr_fon_tn'],
                                      'Fastnr_Org': vals['submission_fa_fastnr_org'],
                                      'MessageRefId': vals['submission_message_ref_id'],
                                      'Timestamp': vals['submission_timestamp'],
                                      'Uebermittlungsart': vals['submission_fa_dr_type'],
                                      'Zeitraum': r.meldungs_jahr},
                                  donation_reports=donation_reports_list)
        assert content, _("prepare(): Could not render the submission content (fo_donation_report_j2template.xml) "
                          "for donation report submission %s with vals:\n%s") % (r.id, vals)
        # TODO: Validate if the content is valid xml and can be decoded to utf8!
        vals.update({'submission_content': content})

        # Return the dict with the submission values
        logger.info("compute_submission_values() END")
        return vals

    # Helper method to clear the correct fields of the submission by state
    @api.multi
    def update_submission(self, **f):
        assert self.ensure_one(), _("update_submission() will only work for one record at at time!")
        assert f.get('state', False), "update_submission(): 'state' must be set in fields!"
        logger.info("update_submission() START")

        # Pre submission errors
        # ---------------------
        error_fields = ['error_type', 'error_code', 'error_detail']
        if any(key in f for key in error_fields):
            assert f['state'] == 'error', "state must be 'error' if any field of %s is to be updated" % error_fields
        error_type = f.get('error_type', False)
        error_code = f.get('error_code', False)
        error_detail = f.get('error_detail', False)
        f.update({'error_type': error_type,
                  'error_code': error_code,
                  'error_detail': error_detail,
                  })

        # Reset the donation reports for pre submission known errors
        # ----------------------------------------------------------
        if f['state'] == 'error' and self.donation_report_ids:
            logger.info("update_submission() Set %s donation reports to state 'new'!" % len(self.donation_report_ids))
            self.donation_report_ids.write({'state': 'new', 'submission_id_datetime': False})

        # Response errors
        # ---------------
        response_error_fields = ['response_error_type', 'response_error_code', 'response_error_detail',
                                 'response_error_orig_refnr']
        response_error_type = f.get('response_error_type', False)
        response_error_code = f.get('response_error_code', False)
        response_error_detail = f.get('response_error_detail', False)
        response_error_orig_refnr = f.get('response_error_orig_refnr', False)
        f.update({
            'response_error_type': response_error_type,
            'response_error_code': response_error_code,
            'response_error_detail': response_error_detail,
            'response_error_orig_refnr': response_error_orig_refnr,
        })

        # Request duration
        f.update({
            'request_duration': f.get('request_duration', False) or self.request_duration,
        })

        # Update the submission log with state and error information if any
        if f.get('submission_log', False):
            # Always append to the existing submission log of the donation report submission
            submission_log = self.submission_log or ''

            # Append submission_log from kwargs
            submission_log += f['submission_log']

            # Append log with state and error information
            submission_log += "state: %s\n" % f['state']
            all_error_fields = error_fields + response_error_fields
            for error_f in all_error_fields:
                if locals().get(error_f, False):
                    submission_log += "%s:\n%s\n" % (error_f, locals().get(error_f))
            submission_log += "----------------------------------------\n\n"

            # update submission log in f
            f['submission_log'] = submission_log

        # Update the submission
        # ---------------------
        logger.info("update_submission() Update the donation report submission!")
        self.write(f)
        logger.info("update_submission() END")
        return

    @api.multi
    def prepare(self):
        for r in self:
            logger.info("prepare() START")
            # CHECK the report state
            if r.state not in ['new', 'prepared', 'error']:
                raise ValidationError(_("You can not prepare or update a submission in state %s!") % r.state)

            # CHECK if submission_fa_art is UEB_SA which stands for Sonderausgaben
            if r.submission_fa_art != 'UEB_SA':
                raise ValidationError(_("The Uebermittlungsbereich (art) must be 'UEB_SA' for Sonderausgaben!"))

            # CHECK if all mandatory fields are set
            missing_mandatory_fields = [f for f in r.mandatory_fields() if not r[f]]
            if missing_mandatory_fields:
                r.update_submission(state='error', error_type='data_incomplete',
                                    error_detail="Missing Fields: %s" % missing_mandatory_fields)
                continue

            # COMPUTE THE SUBMISSION VALUES
            # -----------------------------
            logger.info("prepare() Computing sumbission values!")
            try:
                vals = r.compute_submission_values()
            except Exception as e:
                r.update_submission(state='error', error_type='preparation_error',
                                    error_code='compute_submission_values_exception', error_detail=repr(e))
                continue

            # Check the submission values for completeness
            # --------------------------------------------
            logger.info("prepare() Check the computed sumbission values!")
            empty_vals = [k for k in vals if not vals[k]]
            if empty_vals:
                r.update_submission(state='error', error_type='preparation_error',
                                    error_code='submission_values_missing',
                                    error_detail="Missing Submission Fields:\n%s" % empty_vals)
                continue

            # Preparation successful
            logger.info("prepare() Preparation of donation report submission was successful! "
                        "Finally updating the submission and link and update the donation reports!")
            r.update_submission(state='prepared', **vals)
            logger.info("prepare() END")
            continue

    @api.multi
    def submit(self):
        for r in self:
            logger.info("Donation report submission (ID %s) is going to be submitted!" % r.id)
            # Check the state of the submission:
            assert r.state in ['new', 'prepared', 'error'], _("(Re)Submission to FinanzOnline is not allowed in state "
                                                              "%s") % r.state

            # Only allow production submission if we are on a production server
            if r.submission_env != 'T' and not is_production_server():
                dev_srv_error_msg = ("Submission of production (P) donation report submissions is only allowed on "
                                     "production servers!")
                logger.error(dev_srv_error_msg)
                raise ValidationError(dev_srv_error_msg)

            # Check that a maximum of 10000 donation reports is not exceeded
            if len(r.donation_report_ids) > 10000:
                r.update_submission(state='error', error_type='donation_report_limit',
                                    error_code='',
                                    error_detail="A maximum of 10000 donation reports are allowed per submission!")
                continue

            # Check if the submission values have changed
            # -------------------------------------------
            try:
                vals = r.compute_submission_values()
            except Exception as e:
                r.update_submission(state='error', error_type='changes_after_prepare',
                                    error_code='compute_submission_values_exception', error_detail=repr(e))
                continue
            if not vals:
                r.update_submission(state='error', error_type='changes_after_prepare',
                                    error_code='compute_submission_values_empty',
                                    error_detail="Could not compute submission values! "
                                                 "Maybe there where no donation reports found?")
                continue
            # Compare most fields
            changed_submission_fields = [k for k in vals
                                         if k not in ['donation_report_ids',
                                                      'submission_content',
                                                      'submission_timestamp'] and vals[k] != r[k]]
            # Compare submission_content (which will indirectly shows if the donation_report_ids stayed the same)
            submission_content_old = re.sub(r'\<Timestamp\>.*\<\/Timestamp\>', '', r.submission_content)
            submission_content_new = re.sub(r'\<Timestamp\>.*\<\/Timestamp\>', '', vals['submission_content'])
            if submission_content_old != submission_content_new:
                changed_submission_fields += ['submission_content']
            if changed_submission_fields:
                r.update_submission(state='error', error_type='changes_after_prepare',
                                    error_code='submission_information_changed',
                                    error_detail="Submission Data has changed!\n"
                                                 "Please prepare the report again before submission!\n"
                                                 "Fields changed: %s" % changed_submission_fields)
                continue

            # Login to FinanzOnline to get the session id
            # -------------------------------------------
            # HINT: Login will automatically do a logout first!
            error_detail = _('Login to FinanzOnline failed!')
            try:
                fo_session_id = r.bpk_company_id.finanz_online_login()
            except Exception as e:
                error_detail += "\n%s" % repr(e)
                logger.warning(error_detail)
                fo_session_id = False
            if not fo_session_id:
                r.update_submission(state='error', error_type='submission_exception', error_code='login_failed',
                                    error_detail=error_detail)
                continue

            # Prepare Request body(Replace placeholder ###SessionID### with real session id)
            # -------------------------------------------------------------------------------
            request_data = r.submission_content.replace('###SessionID###', fo_session_id, 1)

            # Prepare submission time and log
            # HINT: update_submission() will always append the submission_log to any existing submission_log
            # -------------------------------
            submission_datetime = fields.datetime.now()
            submission_log = "Submission Request on %s:\n" % submission_datetime

            # -------------------------------------------------------------------------------------------------
            # Set all donation reports to state 'submitted' so that they can not be removed from the submission
            # -------------------------------------------------------------------------------------------------
            # HINT: Nothing else needs to be done because we know all reports have the correct infos by
            #       compute_submission_values() above.
            logger.info("Set donation report(s) state to 'submitted' for donation-report-submission (ID %s)!" % r.id)
            r.donation_report_ids.write({'state': 'submitted', 'submission_id_datetime': submission_datetime})

            # -----------------------------------------------------
            # Submit the report to FinanzOnline File Upload Service
            # -----------------------------------------------------
            start_time = time.time()
            try:
                http_header = {
                    'content-type': 'text/xml; charset=utf-8',
                    'SOAPAction': 'upload'
                }
                response = soap_request(url=r.submission_url,
                                        crt_pem=r.bpk_company_id.fa_crt_pem_path,
                                        prvkey_pem=r.bpk_company_id.fa_prvkey_pem_path,
                                        http_header=http_header,
                                        request_data=request_data,
                                        timeout=120)
            except Exception as e:
                # ATTENTION: Maybe this should be an 'unexpected_response' error instead of 'error'
                #            but i think that if there es an exception in 99.9% the file never reached FinanzOnline?
                logger.error(_("Donation report submission (ID %s) exception!\n%s") % (r.id, repr(e)))
                r.update_submission(state='error',
                                    error_type='submission_exception',
                                    error_code='submission_exception',
                                    error_detail="Soap Request Exception!\n%s" % repr(e),
                                    submission_log=submission_log)
                continue

            # Calculate request time
            try:
                request_duration = "%.3f" % (time.time() - start_time)
            except:
                request_duration = False

            # ---------------------
            # Evaluate the response
            # ---------------------

            # Check for an empty response object
            # ----------------------------------
            # HINT: In this case we do not know if the donation reports are submitted to FinanzOnline
            # ATTENTION: Submission will be set to state 'error' by check_response() if no answer file
            #            exist in the DataBox 48 hours after the submission_datetime
            if not response:
                submission_log += "EMPTY RESPONSE OBJECT!\n"
                r.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_no_response',
                                    response_error_code='empty_response_object',
                                    submission_datetime=submission_datetime,
                                    submission_log=submission_log,
                                    request_duration=request_duration)
                continue

            # Prepare submission values
            # -------------------------
            # Get response code and answer
            response_http_code = response.status_code
            response_content = response.content

            # Update submission log with response information
            submission_log += "Response HTTP Status Code: %s\n" % response_http_code
            submission_log += "Response Content:\n%s\n" % response_content

            # Prepare the submission values
            vals = {'submission_datetime': submission_datetime,
                    'submission_log': submission_log,
                    #
                    'response_http_code': response_http_code,
                    'response_content': response_content,
                    'response_content_parsed': False,
                    #
                    'request_duration': request_duration,
                    }

            # Response with error from FinanzOnline
            # -------------------------------------
            # HINT: In this case we expect that the submission was NOT received at all by FinanzOnline
            # HINT: Donation reports can be removed and set to state 'new' from submissions in state 'error'
            if response_http_code != 200:
                r.update_submission(state='error',
                                    error_type='http_code_not_200',
                                    error_code=response_http_code,
                                    error_detail=response_content,
                                    **vals)
                continue

            # Response http code IS 200 but no content
            # ----------------------------------------
            # HINT: In this case we do not know if the donation reports are submitted to FinanzOnline
            # ATTENTION: Submission will be set to state 'error' by check_response() if no answer file
            #            exist in the DataBox 48 hours after the submission_datetime
            if not response.content:
                r.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_no_content',
                                    response_error_code='no_response_content',
                                    **vals)
                continue

            # Evaluate the response content
            # -----------------------------
            try:
                # Try to Parse the content as xml
                parser = etree.XMLParser(remove_blank_text=True)
                response_etree = etree.fromstring(response.content, parser=parser)
                response_pprint = etree.tostring(response_etree, pretty_print=True)
            except Exception as e:
                # Answer could not be parsed
                # --------------------------
                # HINT: In this case we do not know if the donation reports are submitted to FinanzOnline
                # ATTENTION: Submission will be set to state 'error' by check_response() if no answer file
                #            exist in the DataBox 48 hours after the submission_datetime
                r.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_parser',
                                    response_error_detail='Content could not be parsed:\n%s' % repr(e),
                                    **vals)
                continue

            # Add the pretty printed answer to the submission values
            vals['response_content_parsed'] = response_pprint

            # Search for a return code of the file upload service
            returncode = response_etree.find(".//{*}rc")
            returncode = returncode.text if returncode is not None else False
            returnmsg = response_etree.find(".//{*}msg")
            returnmsg = returnmsg.text if returnmsg is not None else response_pprint

            # No return code found in answer
            # ------------------------------
            # HINT: In this case we do not know if the donation reports are submitted to FinanzOnline
            # ATTENTION: Submission will be set to state 'error' by check_response() if no answer file
            #            exist in the DataBox 48 hours after the submission_datetime
            if not returncode:
                r.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_parser',
                                    response_error_detail='Found no return code in answer:\n%s' % response_pprint,
                                    **vals)
                continue

            # FinanzOnline File Upload known ERROR
            # ------------------------------------
            # HINT: In this case we expect that the submission was NOT received at all by FinanzOnline
            # HINT: Donation reports can be removed and set to state 'new' from submissions in state 'error'
            elif returncode != '0':
                r.update_submission(state='error',
                                    error_type=r.file_upload_error_return_codes().get(returncode, 'file_upload_error'),
                                    error_code=returncode,
                                    error_detail=returnmsg,
                                    **vals)
                continue

            # FileUpload was successful (The normal response)
            # -----------------------------------------------
            else:
                r.update_submission(state='submitted', **vals)
                continue

    @api.multi
    def process_response_file(self):
        """
        Process the downloaded response file
        :return: (bool)
        """
        # Check ensure_one()
        assert self.ensure_one(), _("process_response() can only be called for a single record!")
        s = self

        # Make sure there is already a DataBox protocol file (response file) downloaded!
        assert s.response_file, _("process_response() No downloaded response file from FinanzOnline found!")

        # Process the downloaded XML answer file and update submission and donation reports
        # ---------------------------------------------------------------------------------
        # HINT: For processing exceptions we update the submission to state 'unexpected_response'.
        error_msg = _("Parsing of the answer file from FinanzOnline Databox failed!")
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            response_etree = etree.fromstring(s.response_file.encode('utf-8'), parser=parser)
            if not len(response_etree):
                raise ValidationError(_("Empty content after xml parsing of the DataBox response file!"))
        except Exception as e:
            error_msg += "\n%s" % repr(e)
            logger.error(error_msg)
            s.update_submission(state='unexpected_response',
                                response_error_type='unexpected_parser',
                                response_error_detail=error_msg)
            return True

        # Get the <Info> element
        info = response_etree.find(".//{*}Info")
        info = info.text if info is not None else ''

        # Unexpected Result
        if not info or info not in ['OK', 'NOK', 'TWOK']:
            error_msg = _("Unexpected <Info> content: %s") % info
            logger.error(error_msg)
            s.update_submission(state='unexpected_response',
                                response_error_type='unexpected_parser',
                                response_error_detail=error_msg)
            return True

        # Submission was completely accepted
        if info == "OK":
            state = "response_ok"
            # Update donation reports and the submission
            s.donation_report_ids.write({'state': state,
                                         'submission_id_datetime': s.submission_datetime,
                                         'response_content': False,
                                         'response_error_code': False,
                                         'response_error_detail': False})
            s.update_submission(state=state)
            return True

        # Submission was completely rejected
        if info == "NOK":
            state = "response_nok"
            # Try to get the error info
            try:
                code = response_etree.find(".//{*}Code")
                code = code.text if code is not None else ''
                text = response_etree.find(".//{*}Text")
                text = text.text if text is not None else ''
                data = response_etree.find(".//{*}Data")
                data = data.text if data is not None else ''
                if not code:
                    raise ValidationError(_("Error code not found! (ErrorText: %s)") % text)
            except Exception as e:
                error_msg = _("Exception while parsing <Code> and <Text> in answer from DataBox!\n%s") % repr(e)
                logger.error(error_msg)
                s.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_parser',
                                    response_error_detail=error_msg)
                return True
            # Update the donation reports of this submission
            s.donation_report_ids.write({'state': state,
                                         'submission_id_datetime': s.submission_datetime,
                                         'response_content': False,
                                         'response_error_code': code,
                                         })
            # Update the donation report submission
            s.update_submission(state=state,
                                response_error_type='nok',
                                response_error_code=code,
                                response_error_detail=text + data,
                                )
            return True

        # Submission was partially rejected
        if info == "TWOK":
            # HINT: Make sure there are no duplicates in the list because .remove() will only remove the first
            #       occurrence of the value
            remaining_ids = list(set(s.donation_report_ids.ids))
            remaining_ids_length_start = len(remaining_ids)
            # Loop through the TWOK errors: <SonderausgabenError>
            for error_etree in response_etree.iterfind(".//{*}SonderausgabenError"):
                refnr = error_etree.find(".//{*}RefNr").text
                code = error_etree.find(".//{*}Code").text
                text = error_etree.find(".//{*}Text").text
                if not all((refnr, code, text)):
                    raise ValidationError(_("Data missing for SonderausgabenError! RefNr %s, Code %s, Text %s"
                                            "") % (refnr, code, text))

                # Get <Data> if available to get the original RefNr. for ERR-U-008 errors
                data = error_etree.find(".//{*}Data")
                data = data.text if data is not None else False

                # Find related donation report
                dr = s.env['res.partner.donation_report'].sudo().search(
                    [('submission_id', '=', s.id),
                     ('submission_refnr', '=', refnr)])
                if not dr or len(dr) != 1:
                    raise ValidationError(_("None or multiple donation reports found (IDs %s) for SonderausgabenError: "
                                            "RefNr %s, Code %s, Text %s"
                                            "") % (dr.ids if dr else '', refnr, code, text))

                # Compute content
                try:
                    content = etree.tostring(error_etree, encoding='utf-8')
                    if content:
                        content = content.decode('utf-8')
                    else:
                        content = False
                except:
                    content = False

                # Update the rejected donation report
                dr.write({'state': 'response_nok',
                          'submission_id_datetime': s.submission_datetime,
                          'response_content': content,
                          'response_error_code': code,
                          'response_error_detail': text + ' ' + data if data else text,
                          'response_error_orig_refnr': data if data and 'ERR-U-008' in code else False})

                # Remove the id from the remaining_ids donation reports list
                remaining_ids.remove(dr.id)

            # Check that we found at least one rejected donation reports for this TWOK submission
            if remaining_ids and len(remaining_ids) >= remaining_ids_length_start:
                raise ValidationError("Answer from ZMR is partially rejected (TWOK) but no donation reports "
                                      "with errors could be found!?")

            # Update the accepted donation reports
            if remaining_ids:
                ok_reports = s.env['res.partner.donation_report'].sudo().browse(remaining_ids)
                ok_reports.write({'state': 'response_ok',
                                  'submission_id_datetime': s.submission_datetime,
                                  'response_content': False,
                                  'response_error_code': False,
                                  'response_error_detail': False})

            # Update the donation report submission
            s.update_submission(state='response_twok',
                                response_error_type='twok',
                                response_error_code=False,
                                response_error_detail=False)
            return True

    @api.multi
    def check_response(self):
        """
        Check the answer file from the Databox of FinanzOnline and update the submission and it's donation reports
        based on the downloaded file!

        :return: (bool)
        """
        # Check ensure_one()
        assert self.ensure_one(), _("check_response() can only be called for a single record!")
        s = self

        # Check if we are in a correct state ('submitted' or 'unexpected_response')
        if s.state not in ['submitted', 'unexpected_response']:
            raise ValidationError(_("It is not possible to check FinanzOnline Databox response in state %s") % s.state)

        # Try to get the last submission date
        if not s.submission_datetime and s.state == 'unexpected_response':
            # HINT: This is a hack to get the latest submission_datetime from the submission log
            #       This is necessary because submission_datetime was not stored for empty responses earlier
            # HINT: [-1] will get only the last result from findall
            submission_datetime = ''.join(re.findall(
                ur"(?u)(?<=Submission Request on )\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", s.submission_log
            )[-1])
            submission_datetime = fields.datetime.strptime(submission_datetime, '%Y-%m-%d %H:%M:%S')
        else:
            submission_datetime = fields.datetime.strptime(s.submission_datetime, fields.DATETIME_FORMAT)

        # Check if the Submission date of the donation report is not older than 31 days
        # HINT: Only documents that are 31 days or less can be listed and downloaded from the databox
        download_deadline = submission_datetime + datetime.timedelta(days=30)
        if fields.datetime.now() > download_deadline:
            error_msg = _("The answer protocol for submission with ID %s can only be downloaded from the FinanzOnline "
                          "Databox for 31 days via an webservice request!") % s.id
            logger.error(error_msg)
            raise ValidationError(error_msg)

        # Login to FinanzOnline to get the session id
        # -------------------------------------------
        # HINT: Login will automatically do a logout first!
        error_msg = _('Login to FinanzOnline failed!')
        try:
            fo_session_id = s.bpk_company_id.finanz_online_login()
        except Exception as e:
            error_msg += "\n%s" % repr(e)
            fo_session_id = False
        if not fo_session_id:
            logger.error(error_msg)
            raise ValidationError(error_msg)

        # Get the FileList and download the answer file from the DataBox
        # --------------------------------------------------------------
        if not s.response_file:

            # Render the request body template
            # HINT: A time range of max 7 days is allowed for the file listing!
            addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            soaprequest_templates = pj(addon_path, 'soaprequest_templates')
            fo_databox_getdatabox = pj(soaprequest_templates, 'fo_databox_getdatabox.xml')
            if not os.path.exists(fo_databox_getdatabox):
                raise ValidationError(_("Template fo_databox_getdatabox.xml not found at %s") % fo_databox_getdatabox)
            ts_zust_von = submission_datetime - datetime.timedelta(hours=6)
            ts_zust_bis = submission_datetime + datetime.timedelta(hours=160)
            req_body = render_template(template=fo_databox_getdatabox,
                                       session={'tid': s.bpk_company_id.fa_tid,
                                                'benid': s.bpk_company_id.fa_benid,
                                                'id': fo_session_id},
                                       databox={'erltyp': "P",
                                                'ts_zust_von': ts_zust_von.replace(microsecond=0).isoformat(),
                                                'ts_zust_bis': ts_zust_bis.replace(microsecond=0).isoformat()})

            # Try the 'list files' request to FinanzOnline DataBox
            error_msg = _('List files request to FinanzOnline DataBox failed!')
            try:
                http_header = {
                    'content-type': 'text/xml; charset=utf-8',
                    'SOAPAction': 'getDatabox'
                }
                response = soap_request(url="https://finanzonline.bmf.gv.at/fon/ws/databox",
                                        crt_pem=s.bpk_company_id.fa_crt_pem_path,
                                        prvkey_pem=s.bpk_company_id.fa_prvkey_pem_path,
                                        http_header=http_header, request_data=req_body,
                                        timeout=120)
            except Exception as e:
                error_msg += "\n%s" % repr(e)
                raise ValidationError(error_msg)

            # Empty Response
            if not response or not response.content:
                error_msg += _("\nEmpty Response!")
                raise ValidationError(error_msg)

            # Process the answer of the 'getDatabox' request
            error_msg = _('Could not parse the response of the FinanzOnline DataBox list files request!')
            try:
                parser = etree.XMLParser(remove_blank_text=True)
                response_etree = etree.fromstring(response.content, parser=parser)
                response_pprint = etree.tostring(response_etree, pretty_print=True)
            except Exception as e:
                error_msg += "\n%s" % repr(e)
                raise ValidationError(error_msg)

            # Update the databox_listing field!
            s.databox_listing = response_pprint or response.content

            # Try to find the returncode and message
            returncode = response_etree.find(".//{*}rc")
            returncode = returncode.text if returncode is not None else False
            returnmsg = response_etree.find(".//{*}msg")
            returnmsg = returnmsg.text if returnmsg is not None else response_pprint

            # Check if any returncode was found and is not 0
            if not returncode or returncode != "0":
                raise ValidationError(_("Unexpected return code in the answer from DataBox file list request!"
                                        "\n\n%s\n\n%s") % (returnmsg, s.databox_listing))

            # Find and download the correct answer file for this submission
            # HINT: Filename example: "Webservice_UEB_SA_2018-01-29-11.45.07.463000"
            response_file_applkey = False
            response_file = False
            response_file_pretty = False

            # Loop through the listed files in he xml
            for result in response_etree.iterfind(".//{*}result"):
                filebez = result.find(".//{*}filebez")
                filebez = filebez.text if filebez is not None else ''
                logger.info("check_response() Check DataBox File %s" % filebez)
                if "Webservice_UEB_SA".upper() in filebez.upper():
                    applkey = result.find(".//{*}applkey")
                    applkey = applkey.text if applkey is not None else ''
                    if not applkey:
                        raise ValidationError(_("No 'applkey' found for file %s!\n\n%s") % (filebez, result.text))
                    logger.info("Download File '%s' from FinanzOnline DataBox (applkey %s)."
                                "" % (filebez, applkey))

                    # Render the request body template
                    fo_databox_getdataboxentry = pj(soaprequest_templates, 'fo_databox_getdataboxentry.xml')
                    if not os.path.exists(fo_databox_getdataboxentry):
                        raise ValidationError(_("Template fo_databox_getdataboxentry.xml not found at "
                                                                         "%s") % fo_databox_getdataboxentry)
                    req_body = render_template(template=fo_databox_getdataboxentry,
                                               session={'tid': s.bpk_company_id.fa_tid,
                                                        'benid': s.bpk_company_id.fa_benid,
                                                        'id': fo_session_id},
                                               databox={'applkey': applkey})

                    # Download the protocol file from the FinanzOnline DataBox
                    error_msg = _("Download of file %s from FinanzOnline Databox failed!") % filebez
                    try:
                        http_header = {
                            'content-type': 'text/xml; charset=utf-8',
                            'SOAPAction': 'getDataboxEntry'
                        }
                        download = soap_request(url="https://finanzonline.bmf.gv.at/fon/ws/databox",
                                                crt_pem=s.bpk_company_id.fa_crt_pem_path,
                                                prvkey_pem=s.bpk_company_id.fa_prvkey_pem_path,
                                                http_header=http_header, request_data=req_body, timeout=120)
                    except Exception as e:
                        error_msg += "\n%s" % repr(e)
                        raise ValidationError(error_msg)
                    if not download or not download.content:
                        error_msg += "\nEmpty response!"
                        raise ValidationError(error_msg)

                    # Extract and decode the file from the result
                    error_msg = _("Could not decode content of file %s!") % filebez
                    try:
                        download_etree = etree.fromstring(download.content, parser=parser)
                        download_decode = base64.b64decode(download_etree.find(".//{*}result").text)
                        # Convert the download decode string to a unicode string for comparison with unicode
                        # strings (e.g.: s.submission_message_ref_id and s.submission_fa_fastnr_org and alike)
                        if isinstance(download_decode, basestring):
                            download_decode = download_decode.decode('utf-8')
                    except Exception as e:
                        error_msg += "\n%s" % repr(e)
                        raise ValidationError(error_msg)
                    if not download_decode:
                        error_msg += "\nNo file content after base64 decode!"
                        raise ValidationError(error_msg)

                    # Check if the correct submission id is in the file
                    # HINT: Check the submission_fa_fastnr_org also just in case we submit all donation reports with
                    #       one FinanzOnline Teilnehmer and all protocol files for all instances are in one DataBox
                    if s.submission_message_ref_id in download_decode and s.submission_fa_fastnr_org in download_decode:
                        response_file_applkey = applkey
                        response_file = download_decode
                        try:
                            prs = etree.XMLParser(remove_blank_text=True)
                            response_file_etree = etree.fromstring(response_file.encode('utf-8'), parser=prs)
                            response_file_pprint = etree.tostring(response_file_etree, pretty_print=True)
                            response_file_pretty = response_file_pprint
                        except Exception as e:
                            logger.error("Could not parse the databox response_file as xml!\n%s" % repr(e))
                            pass
                        break

            # No response file could be found
            if not response_file:
                # HINT: If we can not find a response file for a submission in state 'unexpected_response'
                #       24 Hours after it's submission we consider it as not received by FinanzOnline and therefore
                #       change the state to 'error'
                if s.state == 'unexpected_response':
                    if datetime.datetime.now() > submission_datetime + datetime.timedelta(hours=24):
                        msg = "No response file found after 24 hours for donation report submission in state " \
                              "'unexpected_response'! Setting state of submission to 'error'!"
                        logger.warning(msg)
                        s.update_submission(state='error',
                                            error_type='file_upload_error',
                                            error_code=False,
                                            error_detail=msg,
                                            submission_log=msg)
                        return True
                else:
                    raise ValidationError("No protocol file found in FinanzOnline DataBox for this submission! "
                                          "Please try again later!")

            # Force update the response_file
            s.response_file_applkey = response_file_applkey
            s.response_file = response_file
            s.response_file_pretty = response_file_pretty

        # Process the response file
        if s.process_response_file():
            return True

        # If we reached this point something went awfully wrong!
        raise ValidationError("check_response() Sorry but something went wrong! Please contact the support!")

    # First simple implementation
    @api.multi
    def release_donation_reports(self):
        if not self or not self.ensure_one():
            raise ValidationError(_("release_donation_reports() works only for single records!"))
        s = self
        if s.state == 'response_nok' and 'ERR-F-' in s.response_error_code:
            s.donation_report_ids.write({'state': 'error',
                                         'submission_id': False,
                                         'error_type': 'nok_released',
                                         'error_code': False,
                                         'error_detail': "Released from rejected submission: %s" % s.id,
                                         'response_content': False,
                                         'response_error_code': False,
                                         'response_error_detail': False})
        else:
            raise ValidationError(_("You can not release donation reports for a submission in state %s or without "
                                    "'ERR-F-...' in response_error_code!") % s.state)

    # ------------------------------------------
    # SCHEDULER ACTIONS FOR AUTOMATED PROCESSING
    # ------------------------------------------
    # HINT: This should be started every day and then get the Meldezeitraum from the account.fiscalyear!
    #       It checks if it needs to be run at all (inside Meldezeitraum) for every possible
    #       Meldejahr (now - 6 Years) and if the current day is the correct Meldetag for this instance
    @api.model
    def scheduled_submission(self):
        logger.info("scheduled_submission() START")
        now = fields.datetime.utcnow()

        def prepare(subm):
            subm_info = "ID='%s', NAME='%s'" % (subm.id, subm.name)
            logger.info("scheduled_submission() Prepare donation-report-submission %s" % subm_info)

            # Prepare messages
            msg_error = "scheduled_submission() ERROR: Prepare donation-report-submission failed! %s" % subm_info

            try:
                subm.prepare()
            except Exception as e:
                msg = "%s\n\n%s" % (msg_error, repr(e))
                logger.error(msg)
                send_internal_email(odoo_env_obj=subm.env, subject=msg_error, body=msg)
                return False

            if subm.state != 'prepared':
                logger.error(msg_error)
                body = "%s\n\n%s\n\n%s\n\n%s\n\n" % (msg_error, subm.error_type, subm.error_code, subm.error_detail)
                send_internal_email(odoo_env_obj=subm.env, subject=msg_error, body=body)
                return False

            rep_count = 0 if not subm.donation_report_ids else len(subm.donation_report_ids)
            subm_info = "ID='%s', NAME='%s', REPS='%s'" % (subm.id, subm.name, rep_count)
            msg_success = "scheduled_submission() SUCCESS: Prepared donation-report-submission! %s" % subm_info
            send_internal_email(odoo_env_obj=subm.env, subject=msg_success, body=msg_success)
            logger.info(msg_success)
            return True

        def submit(subm):
            report_count = 0 if not subm.donation_report_ids else len(subm.donation_report_ids)
            subm_info = "ID='%s', NAME='%s', REPS='%s'" % (subm.id, subm.name, report_count)
            logger.info("scheduled_submission() Submit donation-report-submission %s to FinanzOnline" % subm_info)

            # ATTENTION: Do NOT send the submission if we are on a dev server!
            if not is_production_server():
                logger.warning("Will not auto-submit donation-report-submission (ID %s) on a development server!"
                               "" % subm.id)
                return False

            # Prepare messages
            msg_error = "scheduled_submission() ERROR: Submission to FinanzOnline FAILED! %s " % subm_info
            msg_success = "scheduled_submission() SUCCESS: Submitted %s to FinanzOnline!" % subm_info

            # Submit the donation report submission to FinanzOnline
            try:
                subm.submit()
            except Exception as e:
                msg = "%s\n\n%s" % (msg_error, repr(e))
                logger.error(msg)
                send_internal_email(odoo_env_obj=subm.env, subject=msg_error, body=msg)
                return False

            if subm.state != 'submitted':
                logger.error(msg_error)
                body = "%s\n\n%s\n\n%s\n\n%s\n\n" % (msg_error, subm.error_type, subm.error_code, subm.error_detail)
                send_internal_email(odoo_env_obj=subm.env, subject=msg_error, body=body)
                return False

            send_internal_email(odoo_env_obj=subm.env, subject=msg_success)
            logger.info(msg_success)
            return True

        # Search for fiscal years
        # HINT: This will get all configured fiscal years for all companies
        spak_start = fields.datetime.strptime('2016-12-01 00:00:00', DEFAULT_SERVER_DATETIME_FORMAT)
        fiscal_years = self.env['account.fiscalyear'].sudo().search([
            ('date_start', '!=', False),
            ('date_stop', '!=', False),
            ('meldezeitraum_start', '!=', False),
            ('meldezeitraum_end', '!=', False),
            ('ze_datum_von', '>=', spak_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
            ('ze_datum_bis', '!=', False),
        ])

        # SKIPP AUTOMATIC SUBMISSION IF NO FISCAL YEAR WAS FOUND
        # ------------------------------------------------------
        if not fiscal_years:
            logger.warning("scheduled_submission() No fiscal year found to auto-generate submission for!")

            # Send internal e-mail if donation reports reports to submit exists but no fiscal year was found
            report_exists = self.env['res.partner.donation_report'].sudo().search([
                ('state', '=', 'new'),
                ('submission_env', '=', 'P'),
            ], limit=1)
            if report_exists:
                msg_error = "scheduled_submission() ERROR: No fiscal year found to auto-generate submission for but " \
                            "donation reports to submit exits!"
                send_internal_email(odoo_env_obj=self.env, subject=msg_error)
            return

        # WARN IF DONATION REPORTS EXISTS THAT DO NOT MATCH ANY FISCAL YEAR WITH MELDEZEITRAUM
        # ------------------------------------------------------------------------------------
        meldungs_jahre = [y.meldungs_jahr for y in fiscal_years if y.meldungs_jahr]
        if meldungs_jahre:
            report_exists = self.env['res.partner.donation_report'].sudo().search([
                ('state', '=', 'new'),
                ('submission_env', '=', 'P'),
                ('meldungs_jahr', 'not in', meldungs_jahre),
            ], limit=1)
            if report_exists:
                msg_error = "scheduled_submission() WARNING: Submittable donation reports exist for non existing or " \
                            "non configured fiscal years!"
                send_internal_email(odoo_env_obj=self.env, subject=msg_error)

        # Process the fiscal years with meldezeitraum
        for y in fiscal_years:

            # SKIPP AUTOMATIC SUBMISSION IF MELDUNGS_JAHR IS NOT SET
            # ------------------------------------------------------
            if not y.meldungs_jahr:
                msg_error = "scheduled_submission() ERROR: meldungs_jahr missing for fiscal year (ID %s)" % y.id
                logger.warning(msg_error)

                # Send a warning e-mail if this fiscal year may be ready to submit
                date_stop = datetime.datetime.strptime(y.date_stop, DEFAULT_SERVER_DATETIME_FORMAT)
                if now < date_stop:
                    send_internal_email(odoo_env_obj=self.env, subject=msg_error)

                continue

            # Check if at least one submittable donation report exists for this fiscal year
            report_exists = self.env['res.partner.donation_report'].sudo().search([
                ('meldungs_jahr', '=', y.meldungs_jahr),
                ('bpk_company_id', '=', y.company_id.id),
                ('submission_id', '=', False),
                ('state', '=', 'new'),
                ('submission_env', '=', 'P'),
            ], limit=1)

            # SKIPP AUTOMATIC SUBMISSION IF NOW IS OUTSIDE OF THE MELDEZEITRAUM
            # -----------------------------------------------------------------
            # HINT: Only fiscal years with meldezeitraum_start and meldezeitraum_end where searched for
            start = datetime.datetime.strptime(y.meldezeitraum_start, DEFAULT_SERVER_DATETIME_FORMAT)
            end = datetime.datetime.strptime(y.meldezeitraum_end, DEFAULT_SERVER_DATETIME_FORMAT)
            if not bool(start <= now <= end):
                logger.info("scheduled_submission() fiscal year %s (ID %s) outside Meldezeitraum"
                            "" % (y.meldungs_jahr, y.id))

                # Send warning if donation reports exists but now is outside of the meldezeitraum
                if report_exists:
                    msg_error = "scheduled_submission() WARNING: fiscal year %s (ID %s) outside Meldezeitraum but " \
                                "donation reports to be submitted exist!" % (y.meldungs_jahr, y.id)
                    send_internal_email(odoo_env_obj=self.env, subject=msg_error)

                continue

            # WARN IF NEXT PLANNED RUN IN FRST IS MORE THAN 24 HOURS IN THE PAST
            # ------------------------------------------------------------------
            # HINT: IF we came this far we know we are inside the meldezeitraum for this fiscal year
            if y.drg_next_run:
                drg_next_run = datetime.datetime.strptime(y.drg_next_run, DEFAULT_SERVER_DATETIME_FORMAT)
                if now > (drg_next_run + datetime.timedelta(hours=24)):
                    msg_error = "scheduled_submission() WARNING: Next planned run in FRST is more than 24 hours in " \
                                "the past for fiscal year %s (ID %s)!" % (y.meldungs_jahr, y.id)
                    logger.warning(msg_error)
                    if report_exists:
                        send_internal_email(odoo_env_obj=self.env, subject=msg_error)
            else:
                msg_error = "scheduled_submission() WARNING: No next planned run in FRST for fiscal year %s (ID %s)!" \
                            "" % (y.meldungs_jahr, y.id)
                logger.warning(msg_error)
                if report_exists:
                    send_internal_email(odoo_env_obj=self.env, subject=msg_error)

            # CHECK LAST REPORT GENERATION IN FRST IF SET
            # -------------------------------------------
            if y.drg_last and y.drg_last_count:
                drg_last = datetime.datetime.strptime(y.drg_last, DEFAULT_SERVER_DATETIME_FORMAT)
                newer_than_drg_last = self.sudo().search([
                    ('meldungs_jahr', '=', y.meldungs_jahr),
                    ('bpk_company_id', '=', y.company_id.id),
                    ('state', 'not in', ['new', 'prepared', 'error']),
                    ('manual', '=', False),
                    ('submission_env', '=', 'P'),
                    ('submission_datetime', '>', y.drg_last),
                    ('create_date', '>', y.drg_last),
                ])

                # SKIPP AUTOMATIC SUBMISSION IF NEWER SUBMISSIONS EXISTS
                if newer_than_drg_last:
                    logger.info("scheduled_submission() Submissions newer than last donation report generation in FRST "
                                "found for meldejahr %s (ID %s). Submission ids: %s. Skipping automatic submission!"
                                "" % (y.meldungs_jahr, y.id, newer_than_drg_last.ids))
                    continue

                # No newer submissions found
                else:
                    new_reports = self.env['res.partner.donation_report'].sudo().search([
                        ('meldungs_jahr', '=', y.meldungs_jahr),
                        ('bpk_company_id', '=', y.company_id.id),
                        ('submission_env', '=', 'P'),
                        ('create_date', '>', y.drg_last),
                    ])

                    # Check if new submissions in FS-Online match the count from Fundraising Studio
                    # HINT: Auto submission scheduled task must be run once a day!
                    if not new_reports or len(new_reports) < y.drg_last_count:

                        # WAIT FOR 24 HOURS IF NEW DONATION REPORTS ARE LESS THAN DRG_LAST_COUNT!
                        if now < (drg_last + datetime.timedelta(hours=24)):
                            logger.info("scheduled_submission() WARNING! There may be unsynced donation reports! "
                                        "Waiting for 24 hours since drg_last for sync to finish! Skipping this "
                                        "meldejahr for next run %s (ID %s)" % (y.meldungs_jahr, y.id))
                            continue

                        # CONTINUE WITH AUTOMATIC SUBMISSION IF STILL TO FEW DONATION REPORTS EXISTS AFTER 24 HOURS
                        # Send a warning and go on with the auto submission
                        else:
                            manual_msg = ("scheduled_submission() WARNING! There may be unsynced donation reports! "
                                          "New reports found in FSON: %s Number of reports created in FRST: %s"
                                          "Existing donation reports will be submitted!"
                                          "" % (len(new_reports), y.drg_last_count))
                            logger.warning(manual_msg)
                            send_internal_email(odoo_env_obj=self.env, subject=manual_msg, body=manual_msg)

            # CHECK INTERVAL RANGE IF INFORMATION OF LAST DONATION REPORT GENERATION IS MISSING
            # ---------------------------------------------------------------------------------
            else:
                last_submitted = self.sudo().search([
                    ('meldungs_jahr', '=', y.meldungs_jahr),
                    ('bpk_company_id', '=', y.company_id.id),
                    ('state', 'not in', ['new', 'prepared', 'error']),
                    ('manual', '=', False),
                    ('submission_env', '=', 'P'),
                    ('submission_datetime', '!=', False),
                ], limit=1, order='submission_datetime DESC')

                # SKIPP AUTOMATIC SUBMISSION IF SUBMISSION(S) EXISTS ALREADY FOR THIS INTERVAL
                if last_submitted:
                    if not y.drg_interval_type or y.drg_interval_type != 'days':
                        msg_error = "scheduled_submission() ERROR: Interval type must be set to 'days' for field " \
                                    "'drg_interval_type'!"
                        logger.error(msg_error)
                        send_internal_email(odoo_env_obj=self.env, subject=manual_msg, body=manual_msg)

                    ls_sd = datetime.datetime.strptime(last_submitted.submission_datetime,
                                                       DEFAULT_SERVER_DATETIME_FORMAT)
                    if now < (ls_sd + datetime.timedelta(days=y.drg_interval_number or 7)):
                        logger.info("scheduled_submission() Skipping auto submission because last submission still"
                                    "in interval range set at fiscal year!")
                        continue

            # CHECK AND WARN FOR UNSUBMITTED MANUAL DONATION REPORT SUBMISSIONS
            # -----------------------------------------------------------------
            manual_not_send = self.sudo().search([
                ('meldungs_jahr', '=', y.meldungs_jahr),
                ('bpk_company_id', '=', y.company_id.id),
                ('state', 'in', ['new', 'prepared', 'error']),
                ('manual', '=', True),
                ('submission_env', '=', 'P'),
            ])
            if manual_not_send:
                manual_msg = ("scheduled_submission() WARNING! Unsubmitted MANUAL donation report submission found! "
                              "(%s)" % manual_not_send.ids)
                logger.warning(manual_msg)
                send_internal_email(odoo_env_obj=self.env, subject=manual_msg)

            # Submit non-manual existing submissions
            # --------------------------------------
            existing = self.sudo().search([
                ('meldungs_jahr', '=', y.meldungs_jahr),
                ('bpk_company_id', '=', y.company_id.id),
                ('state', 'in', ['new', 'prepared', 'error']),
                ('manual', '=', False),
                ('submission_env', '=', 'P'),
            ])
            for s in existing:
                if prepare(s):
                    submit(s)

            # Auto-Submit non linked donation reports
            # ---------------------------------------
            reports = True
            max_subm = 10
            while reports and max_subm > 0:
                max_subm -= 1
                if max_subm <= 0:
                    max_subm_msg = "scheduled_submission() ERROR! Max 'submission per run' limit of 9 exceeded!"
                    logger.error(max_subm_msg)
                    send_internal_email(odoo_env_obj=self.env, subject=max_subm_msg)

                reports = self.env['res.partner.donation_report'].sudo().search([
                    ('meldungs_jahr', '=', y.meldungs_jahr),
                    ('bpk_company_id', '=', y.company_id.id),
                    ('submission_id', '=', False),
                    ('state', '=', 'new'),
                    ('submission_env', '=', 'P'),
                ])

                if reports:
                    # Create new submission
                    new_subm = self.sudo().create(
                        {'submission_env': 'P',
                         'bpk_company_id': y.company_id.id,
                         'meldungs_jahr': y.meldungs_jahr,
                         })
                    # Prepare newly created submission and submit it to FinanzOnline if prepare was successful
                    if prepare(new_subm):
                        submit(new_subm)

        logger.info("scheduled_submission() END")
        return True

    @api.model
    def scheduled_databox_check(self):
        logger.info("scheduled_databox_check() START")

        # Search for submissions in state 'submitted' and 'unexpected_response'
        submitted = self.sudo().search([('state', 'in', ['submitted', 'unexpected_response'])])
        logger.info("scheduled_databox_check() Found %s submitted donation reports" % len(submitted))

        # Check the databox answers
        for r in submitted:
            try:
                logger.info("scheduled_databox_check() Check DataBox answer for %s" % r.submission_message_ref_id)
                r.check_response()
            except (AssertionError, ValidationError) as e:
                logger.error("scheduled_databox_check() ERROR: Check response FAILED!\n%s" % repr(e))

        logger.info("scheduled_databox_check() END")

    # ------------------------
    # Install / Update Methods (called by XML file action records)
    # ------------------------
    # HINT: Called by file: delete_action_on_install_update.xml
    @api.model
    def check_scheduled_tasks(self):
        logger.info("Check if the scheduled task for autom. donation report submission must be renewed.")

        # Recreate odoo scheduler task for autom. donation report submission if interval or type where changed by user
        try:
            task = self.env.ref('fso_con_zmr.ir_cron_scheduled_donation_report_submission')
        except:
            task = False
        if task and (task.interval_number != 1 or task.interval_type != 'days'):
            logger.warning("fso_con_zmr check_scheduled_tasks(). Deleting cron task %s on install/update to "
                           "recreate it with correct values")
            task.unlink()
