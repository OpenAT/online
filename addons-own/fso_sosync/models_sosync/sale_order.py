# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderSosync(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "base.sosync"]

    partner_id = fields.Many2one(sosync="True")
    payment_tx_id = fields.Many2one(sosync="True")
    payment_acquirer_id = fields.Many2one(sosync="True")
    date_order = fields.Datetime(sosync="True")
    amount_total = fields.Float(sosync="True")
    state = fields.Selection(sosync="True")
