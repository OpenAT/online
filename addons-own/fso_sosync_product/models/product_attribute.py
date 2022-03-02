# -*- coding: utf-8 -*-

from openerp import models, fields


class ProductAttributeSosync(models.Model):
    _name = 'product.attribute'
    _inherit = ['product.attribute', 'base.sosync']

    name = fields.Char(sosync="fson-to-frst")
    display_name = fields.Char(sosync="fson-to-frst")

