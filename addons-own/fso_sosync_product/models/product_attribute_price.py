# -*- coding: utf-8 -*-

from openerp import models, fields


class ProductAttributePriceSosync(models.Model):
    _name = 'product.attribute.price'
    _inherit = ['product.attribute.price', 'base.sosync']

    product_tmpl_id = fields.Many2one(sosync="fson-to-frst")
    value_id = fields.Many2one(sosync="fson-to-frst")
    display_name = fields.Char(sosync="fson-to-frst")
    price_extra = fields.Float(sosync="fson-to-frst")
