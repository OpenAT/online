# -*- coding: utf-8 -*-

from openerp import api, models, fields


class CrmFacebookFormField(models.Model):
    _inherit = 'crm.facebook.form.field'

    @api.model
    def facebook_field_type_to_odoo_field_name(self):

        # ATTENTION: super() always needs a second argument or it will return an unbound super object!
        #            https://stackoverflow.com/questions/26788214/super-and-staticmethod-interaction
        res = super(CrmFacebookFormField, self).facebook_field_type_to_odoo_field_name()

        # Append additional fields to the mapping
        # HINT: 'partner_' fields are for the company! 'contact_' fields for the person in crm.lead
        res.update({
            'FIRST_NAME': 'contact_name',
            'LAST_NAME': 'contact_lastname',
            'DOB': 'contact_birthdate_web',
        })

        return res