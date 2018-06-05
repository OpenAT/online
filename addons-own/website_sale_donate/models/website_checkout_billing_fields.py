# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields, api


# new api port
class website_checkout_billing_fields(models.Model):
    _name = 'website.checkout_billing_fields'
    _description = 'Checkout Billing Fields'
    _order = 'sequence, res_partner_field_id'

    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string='Sequence', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage')
    res_partner_field_id = fields.Many2one(comodel_name='ir.model.fields', string="res.partner Field",
                                           domain="[('model_id.model', '=', 'res.partner')]")
    mandatory = fields.Boolean(string='Mandatory')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True)
    validation_rule = fields.Char(string='Validation Rule')
    css_classes = fields.Char(string='CSS classes', default='col-lg-6')
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    information = fields.Html(string='Information', help='Information Text', translate=True)

    # TODO: add nodata and style from auth partner form
    nodata = fields.Boolean(string='NoData', help='Do not pre-fill partner data')
    style = fields.Selection(selection=[('selection', 'Selection'),
                                        ('radio_selectnone', 'Radio + SelectNone'),
                                        ('radio', 'Radio')],
                             string='Field Style')
