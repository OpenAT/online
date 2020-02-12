# -*- coding: utf-8 -*-

from openerp import api, models, fields
from facebeook_lead_to_odoo_lead import facebook_lead_to_odoo_lead_map

class CrmFacebookFormField(models.Model):
    _name = 'crm.facebook.form.field'

    form_id = fields.Many2one('crm.facebook.form', required=True, readonly=True, ondelete='cascade', string='Form')
    label = fields.Char(readonly=True)
    odoo_field = fields.Many2one('ir.model.fields',
                                 domain=[('model', '=', 'crm.lead'),
                                         # ('store', '=', True),
                                         ('ttype', 'in', ('char',
                                                          'date',
                                                          'datetime',
                                                          'float',
                                                          'html',
                                                          'integer',
                                                          'monetary',
                                                          'many2one',
                                                          'selection',
                                                          'phone',
                                                          'text'))],
                                 required=False)
    facebook_field_id = fields.Char(required=True, readonly=True)
    facebook_field_key = fields.Char(required=True, readonly=True)

    _sql_constraints = [
        ('field_unique', 'unique(form_id, odoo_field, facebook_field_key)', 'Mapping must be unique per form')
    ]

    @api.model
    def create(self, values):
        # Auto-map Odoo crm.lead.fields to standard facebook fields
        if 'odoo_field' not in values and 'facebook_field_key' in values:
            ir_fields_obj = self.env['ir.model.fields'].sudo()
            odoo_field_name = facebook_lead_to_odoo_lead_map.get(values['facebook_field_key'])
            odoo_field_rec = ir_fields_obj.search([('model', '=', 'crm.lead'), ('name', '=', odoo_field_name)])

            if odoo_field_rec:
                values['odoo_field'] = odoo_field_rec.id

        record = super(CrmFacebookFormField, self).create(values)

        return record
