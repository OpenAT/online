# -*- coding: utf-'8' "-*-"
from openerp import models, fields

__author__ = 'Michael Karrer'


# Product Acquirer Lines (Link between Products and Acquirers)
class acquirer_lines(models.Model):
    _name = 'product.acquirer_lines'
    _order = 'sequence, acquirer_id'

    sequence = fields.Integer(string='Sequence', default=1000)

    acquirer_id = fields.Many2one(comodel_name='payment.acquirer', string='Payment Acquirer', required=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True)

    acquirer_pre_msg = fields.Html(string="Overwrite Default Acquirer Message", translate=True)


# Product Acquirer
class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    globally_hidden = fields.Boolean(string="Only available for individual Acquirer Config",
                                     help="If set this payment aqcuierer will only show up if explicitly selected in "
                                          "an one page checkout product acquirer configuration but not in the rest of"
                                          "the webshop!")
    product_acquirer_lines_ids = fields.One2many(comodel_name='product.acquirer_lines',
                                                 inverse_name='acquirer_id', string='Product Acquirer Lines')

# Product Template
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_acquirer_lines_ids = fields.One2many(comodel_name='product.acquirer_lines',
                                                 inverse_name='product_id', string='Payment Acquirers Overwrite')
