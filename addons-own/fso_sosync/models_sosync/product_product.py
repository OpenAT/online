# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductProductSosync(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "base.sosync"]

    # This model is read-only in FRST

    default_code = fields.Char(sosync="fson-to-frst")
    product_tmpl_id = fields.Many2one(sosync="fson-to-frst")
    attribute_value_ids = fields.Many2many(sosync="fson-to-frst")
