# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields, api


# new api port
class website_checkout_shipping_fields(models.Model):
    _name = 'website.checkout_shipping_fields'
    _description = 'Checkout Shipping Fields'
    _order = 'sequence, res_partner_field_id'

    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string='Sequence', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage')
    res_partner_field_id = fields.Many2one(comodel_name='ir.model.fields', string="res.partner Field",
                                           domain="[('model_id.model', '=', 'res.partner')]", required=True)
    mandatory = fields.Boolean(string='Mandatory')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True)
    validation_rule = fields.Char(string='Validation Rule')
    css_classes = fields.Char(string='CSS classes', default='col-lg-6')
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    information = fields.Html(string='Information', help='Information Text', translate=True)
