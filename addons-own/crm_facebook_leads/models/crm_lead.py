# -*- coding: utf-8 -*-

from openerp import api, models, fields
import requests
from facebook_graph_api import facebook_graph_api_url


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    facebook_lead_id = fields.Char('Lead ID')
    fb_page_id = fields.Many2one('crm.facebook.page', related='crm_form_id.fb_page_id', store=True,
                                       string='Page', readonly=True)
    fb_form_id = fields.Many2one('crm.facebook.form', string='Form')

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(facebook_lead_id)', 'This Facebook lead already exists!')
    ]

    @api.model
    def get_facebook_leads(self):
        for page in self.env['crm.facebook.page'].search([]):
            forms = self.env['crm.facebook.form'].search([('crm_page_id', '=', page.id),
                                                          ('state', '=', 'active')])
            for form in forms:
                r = requests.get(facebook_graph_api_url + form.fb_form_id + "/leads",
                                 params={'access_token': form.fb_page_access_token}).json()
                if r.get('data'):
                    for lead in r['data']:
                        if not self.search([('facebook_lead_id', '=', lead.get('id')), '|', ('active', '=', True),
                                            ('active', '=', False)]):
                            vals = {}
                            notes = []
                            for field_data in lead['field_data']:
                                if field_data['name'] in form.mappings.filtered(
                                        lambda m: m.odoo_field.id).mapped('facebook_field_key'):
                                    odoo_field = form.mappings.filtered(
                                        lambda m: m.facebook_field_key == field_data['name']).odoo_field
                                    if odoo_field.ttype == 'many2one':
                                        related_value = self.env[odoo_field.relation].search(
                                            [('display_name', '=', field_data['values'][0])])
                                        vals.update({odoo_field.name: related_value and related_value.id})
                                    elif odoo_field.ttype in ('float', 'monetary'):
                                        vals.update({odoo_field.name: float(field_data['values'][0])})
                                    elif odoo_field.ttype == 'integer':
                                        vals.update({odoo_field.name: int(field_data['values'][0])})
                                    elif odoo_field.ttype in ('date', 'datetime'):
                                        vals.update(
                                            {odoo_field.name: field_data['values'][0].split('+')[0].replace('T', ' ')})
                                    elif odoo_field.ttype == 'selection':
                                        vals.update({odoo_field.name: field_data['values'][0]})
                                    else:
                                        vals.update({odoo_field.name: ", ".join(field_data['values'])})
                                else:
                                    notes.append(field_data['name'] + ": " + ", ".join(field_data['values']))
                            if not vals.get('name'):
                                vals.update({'name': form.name + " - " + lead['id']})
                            vals.update({
                                'facebook_lead_id': lead['id'],
                                'description': "\n".join(notes),
                                'section_id': form.section_id and form.section_id.id,
                                'campaign_id': form.campaign_id and form.campaign_id.id,
                                'source_id': form.source_id and form.source_id.id,
                                'medium_id': form.medium_id and form.medium_id.id,
                                'fb_form_id': form.id,
                                'date_open': lead['created_time'].split('+')[0].replace('T', ' ')
                            })
                            lead = self.create(vals)
