# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

import logging
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class ResPartnerFADonationReport(models.Model):
    _name = 'res.partner.donation_report.submission'
    _order = 'submission_datetime DESC'

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

    # Report Type
    # -----------
    # These fields will determine the donation reports that can be added to this DRS (Donation Reports Submission)
    submission_env = fields.Selection(string="Environment", selection=[('t', 'Test'), ('p', 'Production')],
                                      required=True, readonly=True, states={'new': [('readonly', False)]})
    meldungs_jahr = fields.Integer(string="Donation Report Year (Zeitraum)", required=True, size=4,
                                   readonly=True, states={'new': [('readonly', False)]})
    bpk_company_id = fields.Many2one(string="BPK Company", comodel_name='res.company',  required=True,
                                     readonly=True, states={'new': [('readonly', False)]})

    # Donation Reports linked to this Submission
    donation_report_ids = fields.One2many(string="Donation Reports",
                                          comodel_name='res.partner.donation_report', inverse_name="submission_id",
                                          readonly=True, states={'new': [('readonly', False)]})

    # Submission (Request)
    # --------------------
    # HINT: These fields well be "copied" at submission time so that we always know the vales we used for submitting
    #       the donation report submission
    submission_content = fields.Text(string="Submission Content", readonly=True)

    submission_datetime = fields.Datetime(string="Submission Date", readonly=True)
    submission_url = fields.Char(string="Submission URL", readonly=True)

    # This is set by the company from the field res.company > "fa_dr_type"
    # E.g.:  "SO" (SO - Karitative Einrichtungen)
    submission_fa_dr_type = fields.Char(string="Uebermittlungsart", readonly=True)

    submission_fa_tid = fields.Char(string="Teilnehmer Identifikation (tid)", readonly=True)
    submission_fa_benid = fields.Char(string="Webservicebenutzer ID (benid)", readonly=True)
    submission_fa_herstellerid = fields.Char(string="UID-Nummer des Softwareherstellers (herstellerid)",
                                             help="Umsatzsteuer-Identifikations-Nummer (UID-Nummer) des "
                                                  "Softwareherstellers.",
                                             size=24, readonly=True)

    submission_fa_fastnr_org = fields.Char(string="Finanzamt-Steuernummer der Organisation (Fastnr_Org)",
                                           help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus "
                                                "dem Finanzamt (03-98) und aus der Steuernummer (7-stellig) zusammen. "
                                                "(ohne Trennzeichen) (Fastnr_Org)",
                                           size=9)
    submission_fa_fastnr_fon_tn = fields.Char(string="Finanzamt-Steuernummer des Softwareherstellers (Fastnr_Fon_Tn)",
                                              help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus"
                                                   " dem Finanzamt (03-98) und aus der Steuernummer (7-stellig) "
                                                   "zusammen. (ohne Trennzeichen) (Fastnr_Fon_Tn)",
                                              size=9, readonly=True)
    submission_log = fields.Text(string="Submission Log", readonly=True)

    # Response
    # --------
    response_http_code = fields.Char(string="Response HTTP Code")
    response_content = fields.Text(string="Response Content (raw)", readonly=True)
    response_time = fields.Float(string="Response Time (ms)", readonly=True)

    # TODO: Response XML File from FinanzOnline Data Box or from response_content if it is in there?!?
    response_xml_result = fields.Text(string="Response processing result", readonly=True)

    # Error
    # -----
    error_type = fields.Selection(string="Error Type", readonly=True,
                                  selection=[('preparation_error', 'Preparation Error'),
                                             ('data_incomplete', 'Data incomplete'),
                                             ('submission_error', 'Submission Error'),
                                             ('response_error', 'Response Error'),
                                             ])
    error_code = fields.Char(string="Error Code", redonly=True)
    error_detail = fields.Text(string="Error Detail", readonly=True)

    # -------------
    # FIELD METHODS (compute, onchange, constrains)
    # -------------
    # Make sure Fields can not be changed if the donation report submission is in any other state than 'new'
    @api.constrains('submission_env', 'meldungs_jahr', 'bpk_company_id', 'donation_report_ids')
    def _constrain_redonly_if_not_new(self):
        for r in self:
            if r.state != 'new':
                raise ValidationError(_("You can not change the donation report submission in state %s!") % r.state)

    @api.multi
    def prepare(self):
        for r in self:

            # CHECK the report state
            if r.state != 'new':
                raise ValidationError(_("You can not prepare a submission in state %s!") % r.state)

            # CHECK if all mandatory fields are set
            _mandatory_fields = ('submission_env', 'meldungs_jahr', 'bpk_company_id')
            if not all(r[field] for field in _mandatory_fields):
                r.write({'state': 'error', 'error_type': 'data_incomplete', 'error_code': False, 'error_detail': False})
                raise ValidationError(_("Mandatory submission report field(s) %s not set!") % _mandatory_fields)

            # ADD DONATION REPORTS
            # --------------------
            # Search for donation reports
            # HINT: Make sure all the settings of the donation reports match the settings of the submission
            domain = [('state', '=', 'new'),
                      ('submission_id', '=', False),
                      ('submission_env', '=', r.submission_env),
                      ('meldungs_jahr', '=', r.meldungs_jahr),
                      ('bpk_company_id', '=', r.bpk_company_id),
                      ('bpk_state', '=', 'found'),
                      ('bpk_public', '!=', False)]
            donation_report_obj = self.env['res.partner.donation_report']
            donation_reports = donation_report_obj.sudo().search(domain)

            # CHECK for other donation reports which use the same BPK but are for a different partner
            # ATTENTION: This should never find anything because when a donation report is created or updated
            #            this check will also be done in the res.partner.donation_report 'create' and 'write' methods!
            for rep in donation_reports:
                # Search if there is any other donation report with the same BPK but with a different partner
                dups = donation_report_obj.sudo().search([('bpk_private', '=', rep.bpk_private),
                                                          ('bpk_request_company_id', '=', rep.bpk_request_company_id),
                                                          ('bpk_request_partner_id', '!=', rep.bpk_request_partner_id)])
                if dups:

                    # Remove the report from the donation_reports that will be linked to the submission
                    donation_reports = donation_reports - rep

                    # Set the state of all donation reports with the same BPK but different partners to 'error'
                    drs_with_same_bpk_different_partners = dups | rep
                    for dr in drs_with_same_bpk_different_partners:
                        if dr.state == 'new':
                            msg = _("These donation reports do have the same BPK but different partners:\n%s") % (
                                "\n".join(p.name+" (ID "+str(p.id)+')' for p in dups))
                            dr.write({'state': 'error',
                                      'error_type': 'bpk_not_unique', 'error_code': False, 'error_detail': msg})

            # Add the donation reports to the donation report submission
            r.write({'state': 'prepared', 'donation_report_ids': (6, False, donation_reports.ids),
                     'error_type': False, 'error_code': False, 'error_detail': False})
