# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

import os
from os.path import join as pj
from openerp.addons.fso_base.tools.soap import render_template

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
    # ATTENTION: The state error is only valid PRIOR to submission!
    # -------------------------------------------------------------
    error_type = fields.Selection(string="Error Type", readonly=True,
                                  selection=[('data_incomplete', 'Data incomplete'),
                                             ('preparation_error', 'Preparation Error'),
                                             ('changes_after_prepare', 'Preparation data not up to date'),
                                             ('submission_error', 'Submission Error'),
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
                                      selection=[('t', 'Test'), ('p', 'Production')],
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
                                           size=9)

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
    # --------------------------------------------------------------------------------
    submission_url = fields.Char(string="Submission URL", readonly=True,
                                 help=_("The FinanzOnline Webservice URL based on the FinanzOnline Environment "
                                        "(submission_env) which can be either 't' for Test or 'p' for Production!"))
    submission_content = fields.Text(string="Submission Content", readonly=True,
                                     help=_("The rendered template (which is the 'body' of the submission request!)"))

    # Updated at submission
    # ----------------------------------
    submission_datetime = fields.Datetime(string="Last submission request", readonly=True,
                                          help=_("The Date and Time of the last submission request."))
    submission_log = fields.Text(string="Submission Log", readonly=True)

    # Response (updated after submission based on the answer)
    # --------
    response_http_code = fields.Char(string="Response HTTP Code")
    response_content = fields.Text(string="Response Content (raw)", readonly=True)
    response_content_parsed = fields.Text(string="Parsed Response Content (XML)", readonly=True)

    response_error_type = fields.Selection(string="Response Error Type", readonly=True,
                                           selection=[('xxx', 'xxx'),
                                                      ('xxx', 'xxx'),
                                                      ('xxx', 'xxx'),
                                                      ])
    response_error_code = fields.Char(string="Response Error Code", redonly=True)
    response_error_detail = fields.Text(string="Response Error Detail", readonly=True)

    request_duration = fields.Float(string="Request Duration (ms)", readonly=True)

    # --------------
    # HELPER METHODS
    # --------------
    def mandatory_fields(self):
        return 'submission_env', 'meldungs_jahr', 'bpk_company_id', 'submission_fa_art'

    @api.multi
    def prepare(self):
        for r in self:

            # CHECK the report state
            if r.state not in ['new', 'prepared', 'error']:
                raise ValidationError(_("You can not prepare or update a submission in state %s!") % r.state)

            # CHECK if all mandatory fields are set
            missing_mandatory_fields = [f for f in r.mandatory_fields() if not r[f]]
            if missing_mandatory_fields:
                raise ValidationError(_("Mandatory submission field(s) %s not set!") % missing_mandatory_fields)

            # CHECK if submission_fa_art is UEB_SA which stands for Sonderausgaben
            assert r.submission_fa_art == 'UEB_SA', _("The Uebermittlungsbereich (art) must be UEB_SA for "
                                                      "Sonderausgaben!")

            # ADD DONATION REPORTS
            # --------------------
            # Search for donation reports that are not linked to any sumbission
            potential_donation_reports = self.env['res.partner.donation_report'].sudo().search(
                [('state', 'in', ['new', 'error']),
                 ('submission_id', '=', False),
                 ('submission_env', '=', r.submission_env),
                 ('meldungs_jahr', '=', r.meldungs_jahr),
                 ('bpk_company_id', '=', r.bpk_company_id.id)])
            assert potential_donation_reports, _("prepare(): No donation reports found!")

            # Update state and submission information for all found donation reports
            if potential_donation_reports:
                potential_donation_reports.write({})

            # Search again but now only for donation reports in state 'new'
            donation_reports = potential_donation_reports.search(
                [('state', '=', 'new'),
                 ('submission_id', '=', False),
                 ('submission_env', '=', r.submission_env),
                 ('meldungs_jahr', '=', r.meldungs_jahr),
                 ('bpk_company_id', '=', r.bpk_company_id.id)])
            assert donation_reports, _("prepare(): No donation reports found after state and "
                                       "submission information update!")

            # TODO: Check that all donation report company settings match the current company settings
            #       May be to time consuming?: A speed test should be made before implementing it

            # Compute the submission values
            # HINT: submission_fa_login_sessionid is not needed at the preperation stage!
            vals = {
                'state': 'prepared',
                # <fileuploadRequest>
                'submission_fa_tid': r.bpk_company_id.fa_tid,
                'submission_fa_benid': r.bpk_company_id.fa_benid,
                # <data><SonderausgabenUebermittlung><Info_Daten>
                'submission_fa_fastnr_fon_tn': r.bpk_company_id.fa_fastnr_fon_tn,
                'submission_fa_fastnr_org': r.bpk_company_id.fa_fastnr_org,
                # <data><SonderausgabenUebermittlung><MessageSpec>
                'submission_message_ref_id': "Paket%s" % r.id,
                'submission_timestamp': '# TODO TIMESTAMP',
                'submission_fa_dr_type': r.bpk_company_id.fa_dr_type,
                # <data><SonderausgabenUebermittlung><Sonderausgaben> (for loop)
                'donation_report_ids': [(6, 0, donation_reports.ids)],
                # Information copied but not included in the template:
                'submission_fa_herstellerid': r.bpk_company_id.fa_herstellerid,
                #
                'submission_url': '# TODO SUBMISSION URL',
            }

            # Render the request content template
            # -----------------------------------
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
            content = render_template(template=fo_donation_report_j2template,
                                      submission={
                                        'tid': vals['submission_fa_tid'],
                                        'benid': vals['submission_fa_benid'],
                                        'id': '# TODO SessionID',
                                        'art': r.submission_fa_art,
                                        'uebermittlung': r.submission_env,
                                        'Fastnr_Fon_Tn': vals['submission_fa_fastnr_fon_tn'],
                                        'Fastnr_Org': vals['submission_fa_fastnr_org'],
                                        'MessageRefId': vals['submission_message_ref_id'],
                                        'Timestamp': vals['submission_timestamp'],
                                        'Uebermittlungsart': vals['submission_fa_dr_type'],
                                        'Zeitraum': r.meldungs_jahr},
                                      donation_reports=donation_reports_list)
            assert content, _("prepare(): Could not render the content body (fo_donation_report_j2template.xml) "
                              "for donation report submission %s with vals:\n%s") % (r.id, vals)

            # prepare the update
            vals.update({'error_type': False, 'error_code': False, 'error_detail': False,
                         'submission_content': content})

            # Update the donation report submission
            r.write(vals)

    # @api.multi
    # def submit_to_finanzonline(self):
    #     # TODO: If the submission was in state 'prepared' check if there are would be any changes compared to the
    #     #       prepared report and if so stop the submission and set state to error!
