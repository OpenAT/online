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
                                        ('in_progress', 'In Progress'),
                                        ('submitted', 'Submitted'),
                                        ('error', 'Error')])

    # Report Type
    # -----------
    # These fields will determine the donation reports that can be added to this DRS (Donation Reports Submission)
    submission_env = fields.Selection(string="Environment", selection=[('t', 'Test'), ('p', 'Production')],
                                      required=True)
    meldungs_jahr = fields.Integer(string="Donation Report Year (Zeitraum)", required=True, size=4)
    bpk_company_id = fields.Many2one(string="BPK Company", comodel_name='res.company',  required=True)

    # Donation Reports linked to this Submission
    donation_report_ids = fields.One2many(string="Donation Reports", comodel_name='res.partner.donation_report',
                                          inverse_name="submission_id")

    # Submission (Request)
    # --------------------
    submission_content = fields.Text(string="Submission Content", readonly=True)

    submission_datetime = fields.Datetime(string="Submission Date", readonly=True)
    submission_url = fields.Char(string="Submission URL", readonly=True)
    submission_fa_dr_type = fields.Char(string="Uebermittlungsart", readonly=True)

    submission_fa_tid = fields.Char(string="Teilnehmer Identifikation (tid)", readonly=True)
    submission_fa_benid = fields.Char(string="Webservicebenutzer ID (benid)", readonly=True)
    submission_fa_herstellerid = fields.Char(string="Finanzamt-Steuernummer des Softwareherstellers",
                                             help="herstellerid, Fastnr_Fon_Tn", readonly=True)
    submission_fa_orgid = fields.Char(string="Finanzamt-Steuernummer der Organisation",
                                      help="(Fastnr_Org)", readonly=True)
    submission_log = fields.Text(string="Submission Log", readonly=True)

    # Response
    # --------
    response_http_code = fields.Char(string="Response HTTP Code")
    response_content = fields.Text(string="Response Content", readonly=True)
    response_time = fields.Float(string="Response Time (ms)", readonly=True)

    # Error
    # -----
    error_code = fields.Char(string="Error Code", redonly=True)
    error_detail = fields.Text(string="Error Detail", readonly=True)
