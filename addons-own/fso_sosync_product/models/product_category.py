# -*- coding: utf-8 -*-

from openerp import models, fields


class ProductCategorySosync(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'base.sosync']

    name = fields.Char(sosync="fson-to-frst")
    display_name = fields.Char(sosync="fson-to-frst")
