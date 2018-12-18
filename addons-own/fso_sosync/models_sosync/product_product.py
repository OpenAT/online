# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductProductSosync(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "base.sosync"]

    product_tmpl_id = fields.Many2one(sosync="True")
    default_code = fields.Char(sosync="True")
