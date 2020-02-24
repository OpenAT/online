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

    # Computed field to store xml_id to match intervals by unique string in FRST!
    xml_id = fields.Char(string="XML_ID", readonly=True,
                         compute="compute_xml_id", store=True,
                         help="To match correct payment interval in FRST we need an unique string")

    @api.multi
    def compute_xml_id(self):
        records = self or self.search([])
        res = self.get_external_id()
        for record in records:
            record.xml_id = res.get(record.id)

    @api.model
    def compute_all_xml_id(self):
        records = self.search([])
        records.compute_xml_id()


# new api port
class payment_interval_lines(models.Model):
    _name = 'product.payment_interval_lines'
    _order = 'sequence, payment_interval_id'

    sequence = fields.Integer(string='Sequence', default=1000)
    payment_interval_id = fields.Many2one(comodel_name='product.payment_interval', string='Payment Interval',
                                          required=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True)

