# -*- coding: utf-8 -*-

from openerp import api, models, fields


class CrmFacebookFormField(models.Model):
    _name = 'crm.facebook.form.field'

    crm_form_id = fields.Many2one('crm.facebook.form', required=True, readonly=True, ondelete='cascade', string='Form')
    fb_label = fields.Char(readonly=True)
    fb_field_id = fields.Char(required=True, readonly=True)
    fb_field_key = fields.Char(required=True, readonly=True)
    fb_field_type = fields.Char(readonly=True)
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

    _sql_constraints = [
        ('field_unique', 'unique(crm_form_id, crm_field, fb_field_key)', 'Mapping must be unique per form')
    ]

    @staticmethod
    def facebook_field_type_to_odoo_field_name():
        # HINT: 'partner_' fields are for the company! 'contact_' fields for the person in crm.lead
        return {
            'FULL_NAME': 'contact_name',
            'COMPANY_NAME': 'partner_name',
            'TITLE': 'title',
            'EMAIL': 'email_from',
            'PHONE': 'phone',
            'STREET_ADDRESS': 'street',
            'CITY': 'city',
            'POST_CODE': 'zip',
            'STATE': 'state_id',
            'COUNTRY': 'country_id',
            'JOB_TITLE': 'function',
            # 'DOB': '',                  # Date of Birth
            # 'WORK_EMAIL': '',
            # 'WORK_PHONE_NUMBER': '',
        }

    @api.model
    def create(self, values):

        # Auto-map Odoo crm.lead.fields to standard facebook fields
        if 'crm_field' not in values and 'fb_field_type' in values:
            ir_fields_obj = self.env['ir.model.fields']

            crm_field_name = self.facebook_field_type_to_odoo_field_name.get(values['fb_field_type'])
            crm_field_rec = ir_fields_obj.search([('model', '=', 'crm.lead'), ('name', '=', crm_field_name)])
            if crm_field_rec:
                values['crm_field'] = crm_field_rec.id

        record = super(CrmFacebookFormField, self).create(values)
        return record
