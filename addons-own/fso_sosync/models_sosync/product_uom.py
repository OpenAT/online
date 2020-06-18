# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductUomSosync(models.Model):
    _name = "product.uom"
    _inherit = ["product.uom", "base.sosync"]

    # This model is read-only in FRST

    name = fields.Char(sosync="fson-to-frst")
    active = fields.Boolean(sosync="fson-to-frst")
