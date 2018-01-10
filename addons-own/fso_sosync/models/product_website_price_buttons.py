# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductWebsitePriceButtonsSosync(models.Model):
    _name = "product.website_price_buttons"
    _inherit = ["product.website_price_buttons", "base.sosync"]

    name = fields.Char(sosync="True")
    active = fields.Boolean(sosync="True")

    amount = fields.Float(sosync="True")
    sequence = fields.Integer(sosync="True")

    # TO: product.template
    product_id = fields.Many2one(sosync="True")
