# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class AccountFiscalYearSosync(models.Model):
    _name = "account.fiscalyear"
    _inherit = ["account.fiscalyear", "base.sosync"]

    # From odoo
    name = fields.Char(sosync="True")
    code = fields.Char(sosync="True")
    company_id = fields.Many2one(sosync="True")
    date_start = fields.Date(sosync="True")
    date_stop = fields.Date(sosync="True")

    # For donation report submission
    ze_datum_von = fields.Datetime(sosync="True")
    ze_datum_bis = fields.Datetime(sosync="True")
    meldezeitraum_start = fields.Datetime(sosync="True")
    meldezeitraum_end = fields.Datetime(sosync="True")
    drg_interval_number = fields.Integer(sosync="True")
    drg_interval_type = fields.Selection(sosync="True")
    drg_last = fields.Datetime(sosync="True")
