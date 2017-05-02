# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields, api


# new api port
class payment_interval(models.Model):
    _name = 'product.payment_interval'
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence', default=1000)
    name = fields.Text(string='Payment Interval', required=True, translate=True)
    product_template_ids = fields.Many2many(comodel_name='product.template', string='Products')
    payment_interval_lines_ids = fields.One2many(comodel_name='product.payment_interval_lines',
                                                 inverse_name='payment_interval_id', string='Payment Interval Lines')


# new api port
class payment_interval_lines(models.Model):
    _name = 'product.payment_interval_lines'
    _order = 'sequence, payment_interval_id'

    sequence = fields.Integer(string='Sequence', default=1000)
    payment_interval_id = fields.Many2one(comodel_name='product.payment_interval', string='Payment Interval',
                                          required=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True)

