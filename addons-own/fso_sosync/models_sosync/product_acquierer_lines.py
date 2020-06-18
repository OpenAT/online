# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductAcquirerLinesSosync(models.Model):
    _name = "product.acquirer_lines"
    _inherit = ["product.acquirer_lines", "base.sosync"]

    # This model is read-only in FRST

    # TO: payment.acquirer
    acquirer_id = fields.Many2one(sosync="fson-to-frst")

    # TO: product.template
    product_id = fields.Many2one(sosync="fson-to-frst")

    sequence = fields.Integer(sosync="fson-to-frst")
    acquirer_pre_msg = fields.Html(sosync="fson-to-frst")
