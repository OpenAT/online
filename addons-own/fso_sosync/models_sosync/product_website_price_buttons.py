# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductWebsitePriceButtonsSosync(models.Model):
    _name = "product.website_price_buttons"
    _inherit = ["product.website_price_buttons", "base.sosync"]

    # This model is read-only in FRST

    name = fields.Char(sosync="fson-to-frst")

    amount = fields.Float(sosync="fson-to-frst")
    sequence = fields.Integer(sosync="fson-to-frst")

    # TO: product.template
    product_id = fields.Many2one(sosync="fson-to-frst")
