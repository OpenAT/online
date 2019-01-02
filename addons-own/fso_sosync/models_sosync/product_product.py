# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductProductSosync(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "base.sosync"]

    default_code = fields.Char(sosync="True")
    product_tmpl_id = fields.Many2one(sosync="True")
