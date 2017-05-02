# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields, api


# new api port
class product_website_price_buttons(models.Model):
    _name = 'product.website_price_buttons'
    _description = 'Product Website Price Buttons'
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence', default=1000)
    name = fields.Char(string='Name', translate=True)
    amount = fields.Float(string='Amount', required=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True, ondelete='cascade')
    css_classes = fields.Char(string='CSS classes')

