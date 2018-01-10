# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductPaymentIntervalLinesSosync(models.Model):
    _name = "product.payment_interval_lines"
    _inherit = ["product.payment_interval_lines", "base.sosync"]

    # TO: product.payment_interval
    payment_interval_id = fields.Many2one(sosync="True")

    # TO: product.template
    product_id = fields.Many2one(sosync="True")

    sequence = fields.Integer(sosync="True")
