# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductPaymentIntervalLinesSosync(models.Model):
    _name = "product.payment_interval_lines"
    _inherit = ["product.payment_interval_lines", "base.sosync"]

    # This model is read-only in FRST

    # TO: product.payment_interval
    payment_interval_id = fields.Many2one(sosync="fson-to-frst")

    # TO: product.template
    product_id = fields.Many2one(sosync="fson-to-frst")

    sequence = fields.Integer(sosync="fson-to-frst")
