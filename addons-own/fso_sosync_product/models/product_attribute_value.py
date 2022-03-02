# -*- coding: utf-8 -*-

from openerp import models, fields


class ProductAttributeValuesSosync(models.Model):
    _name = 'product.attribute.value'
    _inherit = ['product.attribute.value', 'base.sosync']

    display_name = fields.Char(sosync="fson-to-frst")
    name = fields.Char(sosync="fson-to-frst")
    color = fields.Char(sosync="fson-to-frst")
    price_extra = fields.Float(sosync="fson-to-frst")
    sequence = fields.Integer(sosync="fson-to-frst")
