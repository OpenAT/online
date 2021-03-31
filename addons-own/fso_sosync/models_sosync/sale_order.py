# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderSosync(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "base.sosync"]

    _sync_job_priority = 4000

    # This model is read-only in FRST

    partner_id = fields.Many2one(sosync="fson-to-frst")
    payment_tx_id = fields.Many2one(sosync="fson-to-frst")
    payment_acquirer_id = fields.Many2one(sosync="fson-to-frst")
    date_order = fields.Datetime(sosync="fson-to-frst")
    amount_total = fields.Float(sosync="fson-to-frst")
    state = fields.Selection(sosync="fson-to-frst")

    giftee_partner_id = fields.Many2one(sosync="fson-to-frst")
