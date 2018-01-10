# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductUomSosync(models.Model):
    _name = "product.uom"
    _inherit = ["product.uom", "base.sosync"]

    name = fields.Char(sosync="True")
    active = fields.Boolean(sosync="True")
