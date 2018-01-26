# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError
from openerp.addons.fso_base.tools.soap import render_template, soap_request

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
    _order = 'submission_datetime DESC'

    now = fields.datetime.now

    # ------
    # FIELDS
    # ------
    # HINT: submitted = submitted to FinanzOnline even if we get an
    state = fields.Selection(string="State", readonly=True, default='new',
                             selection=[('new', 'New'),
                                        ('prepared', 'Prepared'),
                                        ('error', 'Error'),
                                        ('submitted', 'Submitted'),
                                        ('response_ok', 'Accepted by FinanzOnline'),
                                        ('response_nok', 'Rejected by FinanzOnline'),
                                        ('response_twok', 'Partially Rejected by FinanzOnline'),
                                        ('unexpected_response', 'Unexpected Response')])

    # Error fields for states 'error'
    # ATTENTION: The state error is only valid PRIOR to submission of for file upload service error!
    # ----------------------------------------------------------------------------------------------
    # HIN File Upload Service error means no data could be submitted so we can retry the submission later
    error_type = fields.Selection(string="Error Type", readonly=True,
                                  selection=[('data_incomplete', 'Data incomplete'),
                                             ('preparation_error', 'Preparation Error'),
                                             ('changes_after_prepare', 'Preparation data not up to date'),
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
    error_code = fields.Char(string="Error Code", redonly=True)
    error_detail = fields.Text(string="Error Detail", readonly=True)

    # Company
    # -----------
    bpk_company_id = fields.Many2one(string="BPK Company", comodel_name='res.company',  required=True,
                                     readonly=True, states={'new': [('readonly', False)]})

    # Submission data computed in the 'prepare' state and updated right before submission
    # -----------------------------------------------------------------------------------
    # <fileuploadRequest>
    submission_fa_tid = fields.Char(string="Teilnehmer Identifikation (tid)", readonly=True)
    submission_fa_benid = fields.Char(string="Webservicebenutzer ID (benid)", readonly=True)
    submission_fa_login_sessionid = fields.Char(string="Session ID (id)", readonly=True)
    submission_fa_art = fields.Selection(string="Uebermitlungsbereich (art)",
                                         selection=[('UEB_SA', 'Sonderausgaben (UEB_SA)')],
                                         default="UEB_SA", readonly=True)
    submission_env = fields.Selection(string="FinanzOnline Environment (uebermittlung)",
                                      default="T",
                                      selection=[('T', 'Test'), ('P', 'Production')],
                                      required=True, readonly=True, states={'new': [('readonly', False)]})

    # <data><SonderausgabenUebermittlung><Info_Daten>
    submission_fa_fastnr_fon_tn = fields.Char(string="Finanzamt-Steuernummer des Softwareherstellers (Fastnr_Fon_Tn)",
                                              help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus"
                                                   " dem Finanzamt (03-98) und aus der Steuernummer (7-stellig) "
                                                   "zusammen. (ohne Trennzeichen) (Fastnr_Fon_Tn)",
                                              size=9, readonly=True)
    submission_fa_fastnr_org = fields.Char(string="Finanzamt-Steuernummer der Organisation (Fastnr_Org)",
                                           help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus "
                                                "dem Finanzamt (03-98) und aus der Steuernummer (7-stellig) zusammen. "
                                                "(ohne Trennzeichen) (Fastnr_Org)",
                                           size=9, readonly=True)

    # <data><SonderausgabenUebermittlung><MessageSpec>
    submission_message_ref_id = fields.Char(string="Paket ID (MessageRefId)", readonly=True)
    submission_timestamp = fields.Char(string="Timestamp (Timestamp)", readonly=True,
                                       help=_("Format: datetime with timezone e.g.: 2012-12-13T12:12:12"))
    submission_fa_dr_type = fields.Char(string="Organisationstyp (Uebermittlungsart)", readonly=True)

    meldungs_jahr = fields.Selection(string="Year", required=True,
                                     help=_("Donation deduction year (Meldejahr)"),
                                     readonly=True, states={'new': [('readonly', False)]},
                                     selection=[(str(i), str(i)) for i in range(2017, int(now().year)+11)])

    # <data><SonderausgabenUebermittlung><Sonderausgaben> (for loop)
    donation_report_ids = fields.One2many(string="Donation Reports",
                                          comodel_name='res.partner.donation_report', inverse_name="submission_id",
                                          readonly=True, states={'new': [('readonly', False)]})

    # Information copied but not included in the template:
    submission_fa_herstellerid = fields.Char(string="UID-Nummer des Softwareherstellers (herstellerid)",
                                             help="Umsatzsteuer-Identifikations-Nummer (UID-Nummer) des "
                                                  "Softwareherstellers.",
                                             size=24, readonly=True)

    # Content and "Submit-to-URL"
    # ---------------------------
    submission_url = fields.Char(string="Submission URL", readonly=True,
                                 default="https://finanzonline.bmf.gv.at/fon/ws/fileupload",
                                 help=_("The FinanzOnline File Upload Webservice URL (static)"))
    submission_content = fields.Text(string="Submission Content", readonly=True,
                                     help=_("The rendered template (which is the 'body' of the submission request!)"))

    # Updated at submission
    # ---------------------
    submission_datetime = fields.Datetime(string="Last submission request", readonly=True,
                                          help=_("The Date and Time of the last submission request."))
    submission_log = fields.Text(string="Submission Log", readonly=True)

    # Response (updated after submission based on the answer)
    # --------
    response_http_code = fields.Char(string="Response HTTP Code", readonly=True)
    response_content = fields.Text(string="Response Content (raw)", readonly=True)
    response_content_parsed = fields.Text(string="Parsed Response Content (XML)", readonly=True)

    response_error_type = fields.Selection(string="Response Error Type", readonly=True,
        selection=[
                   # <Info>NOK</Info> and <Error><Code>ERR-F-*
                   ('nok_fastnr_fon_tn', 'Finanzamt-Steuernummer des Softwareherstellers error (fastnr_fon_tn)'),
                   ('nok_fastnr_org', 'Finanzamt-Steuernummer der Organisation error (fastnr_org)'),
                   ('nok_fastnr_org_year', 'Unauthorized Year (Meldejahr)'),
                   ('nok_fastnr_org_dr_type', 'Unauthorized Organisation-Type (dr_type)'),
                   ('nok_fastnr_fon_tn_access', 'Softwarehersteller not authorized for submission'),
                   ('nok_year', 'Year outside valid range (Meldejahr)'),
                   # <Info>TWOK</Info>
                   ('twok', 'Donation reports partially rejected'),
                   # Unexpected or no response
                   ('unexpected_no_response', 'No Response'),
                   ('unexpected_no_content', 'Response content empty or missing'),
                   ('unexpected_parser', 'Response could not be parsed'),
                   ('unexpected_exception', 'Exception during response processing'),
                   ])
    response_error_code = fields.Char(string="Response Error Code", redonly=True)
    response_error_detail = fields.Text(string="Response Error Detail", readonly=True)

    request_duration = fields.Char(string="Request Duration (seconds)", readonly=True)

    # -------------------
    # ONCHANGE (GUI ONLY)
    # -------------------
    # Only allow to create donation reports for the FinanzOnline Test Environment in the FSON GUI.
    # HINT: Onchange will not be "called" by changes done xmlrpc calls from the sosyncer (TODO Test this ;) )
    @api.onchange('submission_env')
    def _onchange_environment(self):
        for r in self:
            if r.submission_env != "T":
                r.submission_env = "T"
                # raise ValidationError(_("You can only create donation reports submissions for the 'Test' "
                #                         "FinanzOnline environment manually!"))

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
        furc = {'-1': 'session_id',
                '-2': 'service_down_maintenance',
                '-3': 'technical',
                '-4': 'parser',
                '-5': 'file_upload_doctype',
                }
        return furc

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
        # Search for donation reports linked to this submission or not linked at all
        potential_donation_reports = self.env['res.partner.donation_report'].sudo().search(
            [('state', 'in', ['new', 'error']),
             "|", ('submission_id', '=', False),
                  ('submission_id', '=', r.id),
             ('submission_env', '=', r.submission_env),
             ('meldungs_jahr', '=', r.meldungs_jahr),
             ('bpk_company_id', '=', r.bpk_company_id.id)])
        if not potential_donation_reports:
            return {}
        len_pdr = len(potential_donation_reports)
        logger.info("Found %s donation reports to check and update for submission %s" % (len_pdr, r.id))

        # Update state and submission information for all found donation reports
        logger.info("Update state and submission information for %s donation reports!" % len_pdr)
        potential_donation_reports.write({})
        logger.info("Update state and submission information for %s donation reports done!" % len_pdr)

        # Search again but now only for donation reports in state 'new'
        donation_reports = potential_donation_reports.search(
            [('state', '=', 'new'),
             "|", ('submission_id', '=', False),
                  ('submission_id', '=', r.id),
             ('submission_env', '=', r.submission_env),
             ('meldungs_jahr', '=', r.meldungs_jahr),
             ('bpk_company_id', '=', r.bpk_company_id.id)])
        if not donation_reports:
            return {}
        len_dr = len(donation_reports)
        logger.info("Found %s donation reports for submission %s after donation report update!" % (len_dr, r.id))

        # Compute the basic submission values
        # HINT: submission_fa_login_sessionid is only computed and needed right before submission!
        # ATTENTION: submission_timestamp is used for the PREPARATION time of the submission values and NOT
        #            the time of the report submission try!!!
        vals = {
            # <fileuploadRequest>
            'submission_fa_tid': r.bpk_company_id.fa_tid,
            'submission_fa_benid': r.bpk_company_id.fa_benid,
            # <data><SonderausgabenUebermittlung><Info_Daten>
            'submission_fa_fastnr_fon_tn': r.bpk_company_id.fa_fastnr_fon_tn,
            'submission_fa_fastnr_org': r.bpk_company_id.fa_fastnr_org,
            # <data><SonderausgabenUebermittlung><MessageSpec>
            'submission_message_ref_id': "SUBMID%s" % r.id,
            'submission_timestamp': fields.datetime.utcnow().replace(microsecond=0).isoformat(),
            'submission_fa_dr_type': r.bpk_company_id.fa_dr_type,
            # <data><SonderausgabenUebermittlung><Sonderausgaben> (for loop)
            'donation_report_ids': [(6, 0, donation_reports.ids)],
            # Information copied but not included in the jinja2 template:
            'submission_fa_herstellerid': r.bpk_company_id.fa_herstellerid,
            # FinanzOnline File Upload Webservice URL
            'submission_url': r.submission_url,
        }

        # Render the request content template and add it to the submission vals
        # ---------------------------------------------------------------------
        # Get the path to the template 'fo_donation_report_j2template.xml '
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        fo_donation_report_j2template = pj(soaprequest_templates, 'fo_donation_report_j2template.xml')
        assert os.path.exists(fo_donation_report_j2template), _("fo_donation_report_j2template.xml not found at "
                                                                "%s") % fo_donation_report_j2template

        # Prepare the donation reports as a list with nested dicts for the jinja2 template
        donation_reports_list = [{'sub_typ': do_rep.submission_type,
                                  'RefNr': do_rep.submission_refnr,
                                  'Betrag': "%.2f" % do_rep.betrag,
                                  'vbPK': do_rep.submission_bpk_public} for do_rep in donation_reports]

        # Render the template for the request content (body)
        # ATTENTION: !!! '###SessionID###' will be replaced by submit() with the correct session id !!!
        #            So do not change this here!
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
        # TODO: Validate if the content is valid xml and could be decoded to utf8!
        vals.update({'submission_content': content})

        # Return the dict with the submission values
        return vals

    # Helper method to clear the correct fields of the submission by state
    @api.multi
    def update_submission(self, **f):
        assert self.ensure_one(), _("update_submission() will only work for one record at at time!")
        assert f.get('state', False), "update_submission(): 'state' must be set in fields!"

        # Pre submission errors
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

        # # Clean submission fields in new or error state EXCEPT for the linked donation reports.
        # if f['state'] in ['error', 'new']:
        #     f.update({'submission_fa_tid': False,
        #               'submission_fa_benid': False,
        #               'submission_fa_login_sessionid': False,
        #               'submission_fa_art': False,
        #               'submission_fa_fastnr_fon_tn': False,
        #               'submission_fa_fastnr_org': False,
        #               'submission_message_ref_id': False,
        #               'submission_timestamp': False,
        #               'submission_fa_dr_type': False,
        #               'submission_fa_herstellerid': False,
        #               })

        # Response errors
        response_error_fields = ['response_error_type', 'response_error_code', 'response_error_detail']
        response_error_type = f.get('response_error_type', False)
        response_error_code = f.get('response_error_code', False)
        response_error_detail = f.get('response_error_detail', False)
        f.update({
            'response_error_type': response_error_type,
            'response_error_code': response_error_code,
            'response_error_detail': response_error_detail,
        })

        # Request duration
        f.update({
            'request_duration': f.get('request_duration', False),
        })

        # Update the submission log with state and error information if any
        submission_log = f.get('submission_log', False)
        if submission_log:
            submission_log += "state: %s\n" % f['state']
            all_error_fields = error_fields + response_error_fields
            for error_f in all_error_fields:
                if locals().get(error_f, False):
                    submission_log += "%s:\n%s\n" % (error_f, locals().get(error_f))
            submission_log += "----------------------------------------\n\n"

        # Update the submission
        # ---------------------
        self.write(f)
        return

    @api.multi
    def prepare(self):
        for r in self:
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
            try:
                vals = r.compute_submission_values()
            except Exception as e:
                r.update_submission(state='error', error_type='preparation_error',
                                    error_code='compute_submission_values_exception', error_detail=repr(e))
                continue

            # Check the submission values for completeness
            # --------------------------------------------
            empty_vals = [k for k in vals if not vals[k]]
            if empty_vals:
                r.update_submission(state='error', error_type='preparation_error',
                                    error_code='submission_values_missing',
                                    error_detail="Missing Submission Fields:\n%s" % empty_vals)
                continue

            # Preparation successful
            r.update_submission(state='prepared', **vals)
            continue

    @api.multi
    def submit(self):
        for r in self:
            logger.info("Donation report submission (ID %s) is going to be submitted!" % r.id)

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
                                    error_detail="Could not compute up to date submission values for comparision!")
                continue
            # Compare most fields
            changed_submission_fields = [k for k in vals
                                         if vals[k] != r[k] and k not in ['donation_report_ids',
                                                                          'submission_content',
                                                                          'submission_timestamp']]
            # Compare submission_content (which will indirectly shows if the donation_report_ids stayed the same)
            submission_content_old = re.sub(r'\<Timestamp\>.*\<\/Timestamp\>', '', r.submission_content)
            submission_content_new = re.sub(r'\<Timestamp\>.*\<\/Timestamp\>', '', vals['submission_content'])
            if submission_content_old != submission_content_new:
                changed_submission_fields += ['submission_content']
            if changed_submission_fields:
                r.update_submission(state='error', error_type='changes_after_prepare',
                                    error_code='submission_information_changed',
                                    error_detail="Submission Data has changed!\nPlease prepare the report again before "
                                                 "submission!\nFields changed: %s" % changed_submission_fields)
                continue

            # Login to FinanzOnline and update the session id and request_data
            # ----------------------------------------------------------------
            try:
                r.bpk_company_id.finanz_online_logout()
            except Exception as e:
                logger.warning(_("Logout from FinanzOnline failed:\n%s") % repr(e))
            try:
                fo_session_id = r.bpk_company_id.finanz_online_login()
            except Exception as e:
                logger.warning(_("Login to FinanzOnline failed:\n%s") % repr(e))
                fo_session_id = False
            if not fo_session_id:
                r.update_submission(state='error', error_type='submission_exception', error_code='login_failed',
                                    error_detail="Login to FinanzOnline failed")
                continue
            # Replace placeholder ###SessionID### with real session id
            request_data = r.submission_content.replace('###SessionID###', fo_session_id, 1)

            # Set all donation reports to state 'submitted' so that they can not be removed from the submission
            # -------------------------------------------------------------------------------------------------
            # HINT: Nothing else needs to be done because we know all reports have the correct computed infos now
            logger.info("Set donation report(s) state to 'submitted' for donation-report-submission (ID %s)!" % r.id)
            r.donation_report_ids.write({'state': 'submitted'})

            # Submit the report to FinanzOnline File Upload Service
            # -----------------------------------------------------
            start_time = time.time()
            submission_datetime = fields.datetime.now()
            submission_log = r.submission_log or ''
            submission_log += "Submission Request on %s:\n" % submission_datetime
            try:
                http_header = {
                    'content-type': 'text/xml; charset=utf-8',
                    'SOAPAction': 'upload'
                }
                response = soap_request(url=r.submission_url, http_header=http_header, request_data=request_data,
                                        timeout=120)
            except Exception as e:
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

            # Check for an empty response object
            # ----------------------------------
            if not response:
                submission_log += "EMPTY RESPONSE OBJECT!\n"
                r.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_no_response',
                                    response_error_code='empty_response_object',
                                    submission_log=submission_log,
                                    request_duration=request_duration)
                continue

            # Update submission log with response data
            # ----------------------------------------
            submission_log += "Response HTTP Status Code: %s\n" % response.status_code
            submission_log += "Response Content:\n%s\n" % response.content

            # ------------------
            # Parse the response
            # ------------------
            response_http_code = response.status_code
            response_content = response.content
            vals = {'submission_datetime': submission_datetime,
                    'submission_log': submission_log,
                    'response_http_code': response_http_code,
                    'response_content': response_content,
                    'request_duration': request_duration,
                    }

            # Response http code not 200
            if response.status_code != 200:
                r.update_submission(state='error',
                                    error_type='http_code_not_200',
                                    error_code=response_http_code,
                                    error_detail=response_content,
                                    **vals)
                continue

            # Reponse http code 200 but no content ?!?
            if not response.content:
                r.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_no_content',
                                    response_error_code='no_response_content',
                                    **vals)
                continue

            # Try to parse the response content as xml
            # ----------------------------------------
            try:
                parser = etree.XMLParser(remove_blank_text=True)
                response_etree = etree.fromstring(response.content, parser=parser)
                response_pprint = etree.tostring(response_etree, pretty_print=True)
            except Exception as e:
                r.update_submission(state='unexpected_response',
                                    response_error_type='unexpected_parser',
                                    response_error_detail='Content could not be parsed:\n%s' % repr(e),
                                    **vals)
                continue

            # Search for a return code of the file upload service
            # TODO: Also check if the http error code is not 200 and exit if so
            # TODO: Check if you get a non 200 response even for twok or nok responses!
            # ---------------------------------------------------
            returncode = response_etree.find(".//{*}rc")
            returncode = returncode.text if returncode is not None else False
            returnmsg = response_etree.find(".//{*}msg")
            returnmsg = returnmsg.text if returnmsg is not None else response_pprint
            # File Upload Service error
            if returncode and returncode != '0':
                r.update_submission(state='error',
                                    error_type=r.file_upload_error_return_codes().get(returncode, 'file_upload_error'),
                                    error_code=returncode,
                                    error_detail=returnmsg,
                                    **vals)
                continue

            # TODO: Process the answer xml (ok, nok, twok) and update the donation reports
            # HINT: To get an example of an FinanzOnline Answer i just store the data for now
            # -------------------------------------------------------------------------------
            r.update_submission(state='response_ok', **vals)
            continue
