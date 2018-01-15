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
    state = fields.Selection(string="State", readonly=True, default='new',
                             selection=[('new', 'New'),
                                        ('prepared', 'Prepared'),
                                        ('submitted', 'Submitted'),
                                        ('error', 'Error')])

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
    response_content = fields.Text(string="Response Content", readonly=True)
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
    def _constraion_redonly_if_not_new(self):
        for r in self:
            if r.state != 'new':
                raise ValidationError(_("You can not change the donation report submission in state %s!") % r.state)

