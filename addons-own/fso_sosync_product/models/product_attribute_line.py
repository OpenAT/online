# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

from openerp import models, fields


class ProductAttributeLinesSosync(models.Model):
    _name = 'product.attribute.line'
    _inherit = ['product.attribute.line', 'base.sosync']

    attribute_id = fields.Many2one(sosync="fson-to-frst")
    product_tmpl_id = fields.Many2one(sosync="fson-to-frst")
    display_name = fields.Char("fson-to-frst")
