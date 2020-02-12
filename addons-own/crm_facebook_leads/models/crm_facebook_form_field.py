# -*- coding: utf-8 -*-

from openerp import api, models, fields
from facebeook_lead_to_odoo_lead import facebook_lead_to_odoo_lead_map


class CrmFacebookFormField(models.Model):
    _name = 'crm.facebook.form.field'

    crm_form_id = fields.Many2one('crm.facebook.form', required=True, readonly=True, ondelete='cascade', string='Form')
    fb_label = fields.Char(readonly=True)
    crm_field = fields.Many2one('ir.model.fields',
                                domain=[('model', '=', 'crm.lead'),
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
    fb_field_id = fields.Char(required=True, readonly=True)
    fb_field_key = fields.Char(required=True, readonly=True)

    _sql_constraints = [
        ('field_unique', 'unique(crm_form_id, crm_field, fb_field_key)', 'Mapping must be unique per form')
    ]

    @api.model
    def create(self, values):
        # Auto-map Odoo crm.lead.fields to standard facebook fields
        if 'crm_field' not in values and 'fb_field_key' in values:
            ir_fields_obj = self.env['ir.model.fields'].sudo()
            crm_field_name = facebook_lead_to_odoo_lead_map.get(values['fb_field_key'])
            crm_field_rec = ir_fields_obj.search([('model', '=', 'crm.lead'), ('name', '=', crm_field_name)])

            if crm_field_rec:
                values['crm_field'] = crm_field_rec.id

        record = super(CrmFacebookFormField, self).create(values)

        return record
