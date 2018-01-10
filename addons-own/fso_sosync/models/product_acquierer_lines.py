# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductAcquirerLinesSosync(models.Model):
    _name = "product.acquirer_lines"
    _inherit = ["product.acquirer_lines", "base.sosync"]

    # TO: payment.acquirer
    acquirer_id = fields.Many2one(sosync="True")

    # TO: product.template
    product_id = fields.Many2one(sosync="True")

    sequence = fields.Integer(sosync="True")
    acquirer_pre_msg = fields.Html(sosync="True")
