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
    ze_datum_von = fields.Datetime(sosync="True")               # Spenden / Buchungen included from
    ze_datum_bis = fields.Datetime(sosync="True")               # Spenden / Buchungen included up to

    meldezeitraum_start = fields.Datetime(sosync="True")        # Auto submit start
    meldezeitraum_end = fields.Datetime(sosync="True")          # Auto submit end

    drg_interval_number = fields.Integer(sosync="True")         # FRST scheduler interval number
    drg_interval_type = fields.Selection(sosync="True")         # FRST scheduler interval unit e.g.: days or month

    drg_next_run = fields.Datetime(sosync="True")       # Next scheduled run for donation report checks/generation STP in FRST

    drg_last = fields.Datetime(sosync="True")           # Last scheduled run of the donation report checks/generation STP in FRST
    drg_last_count = fields.Integer(sosync="True")      # Count of donation reports generated at the last scheduled run in FRST

    meldungs_jahr = fields.Char(sosync="True")          # computed field based on ze_datum_von and ze_datum_bis
