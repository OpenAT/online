# -*- coding: utf-8 -*-

from openerp import api, models, fields
import requests
from facebook_graph_api import facebook_graph_api_url

import logging
logger = logging.getLogger(__name__)


class CrmFacebookForm(models.Model):
    _name = 'crm.facebook.form'

    name = fields.Char(required=True, readonly=True)
    active = fields.Boolean(default=True)

    # TODO: New state error and state as computed field (maybe)
    # TODO: Add status "error" to forms and a new field "activated" (Datetime) that will be set when the state
    #       changes from to_review to active and cleared when the state changes to 'to_review' or to 'error'
    state = fields.Selection(selection=[('to_review', 'To review'),
                                        ('active', 'Active'),
                                        ('error', 'Error'),
                                        ('archived', 'Archived')],
                             string='State', required=True, index=True)

    crm_page_id = fields.Many2one('crm.facebook.page', readonly=True, ondelete='cascade', string='Facebook Page')
    fb_form_id = fields.Char(required=True, readonly=True, string='Form ID')
    mappings = fields.One2many('crm.facebook.form.field', 'crm_form_id')

    # team_id does not exist in o8, use crm.case.section instead
    section_id = fields.Many2one('crm.case.section', domain=['|',
                                                             ('use_leads', '=', True),
                                                             ('use_opportunities', '=', True)],
                                 string="Sales Team")
    # UTM
    campaign_id = fields.Many2one('utm.campaign', string='Campaign')
    source_id = fields.Many2one('utm.source', string='Source')
    medium_id = fields.Many2one('utm.medium', string='Medium')

    # Linked Leads
    crm_lead_ids = fields.One2many(comodel_name='crm.lead', inverse_name='crm_form_id', readonly=True)

    @api.multi
    def get_fields(self):
        self.mappings.unlink()
        r = requests.get(facebook_graph_api_url + self.fb_form_id,
                         params={'access_token': self.crm_page_id.fb_page_access_token, 'fields': 'questions'}).json()
        if r.get('questions'):
            for question in r.get('questions'):
                self.env['crm.facebook.form.field'].create({
                    'crm_form_id': self.id,
                    'fb_label': question['label'],
                    'fb_field_id': question['id'],
                    'fb_field_key': question['key'],
                    'fb_field_type': question.get('type', False)
                })

    @api.multi
    def write(self, values):
        # Set the form state according to active, if not already provided
        if 'state' not in values:
            if 'active' in values and not values['active']:
                values['state'] = 'archived'
            else:
                values['state'] = 'to_review'

        # Set form active depending on form state, if not already provided
        if 'active' not in values:
            values['active'] = ('state' in values
                                and values['state'] in ['to_review', 'active'])

        return super(CrmFacebookForm, self).write(values)

    @api.multi
    def facebook_data_to_lead_data(self, facebook_lead_data=None):
        assert self.ensure_one(), "facebook_to_lead_data() supports only one record!"
        assert isinstance(facebook_lead_data, dict), "facebook_lead_data must be a dict!"
        crm_form = self

        # Basic crm.lead lead data
        vals = {
            'fb_lead_id': facebook_lead_data['id'],
            'date_open': facebook_lead_data['created_time'].split('+')[0].replace('T', ' '),
            'description': '',
            'section_id': crm_form.section_id and crm_form.section_id.id,
            'campaign_id': crm_form.campaign_id and crm_form.campaign_id.id,
            'source_id': crm_form.source_id and crm_form.source_id.id,
            'medium_id': crm_form.medium_id and crm_form.medium_id.id,
            'crm_page_id': crm_form.crm_page_id.id,
            'crm_form_id': crm_form.id,
        }

        # Loop through facebook form fields (questions)
        for question in facebook_lead_data['field_data']:
            question_fb_field_key = question.get('name')
            question_val = question['values'][0]

            # Check if the facebook field is mapped to a crm.lead field
            crm_facebook_form_field = crm_form.mappings.filtered(lambda f: f.fb_field_key == question_fb_field_key)

            odoo_field_name = False
            odoo_field_value = False
            # Known (mapped) Fields
            if crm_facebook_form_field:
                odoo_field = crm_facebook_form_field.crm_field
                odoo_field_name = odoo_field.name
                odoo_field_type = odoo_field.ttype

                # Try to find convert question data to valid odoo field data
                try:
                    if odoo_field_type == 'many2one':
                        rec = self.env[odoo_field.relation].search([('display_name', '=', question_val)], limit=1)
                        odoo_field_value = rec.id if rec else False
                    elif odoo_field_type in ('float', 'monetary'):
                        odoo_field_value = float(question_val)
                    elif odoo_field_type == 'integer':
                        odoo_field_value = int(question_val)
                    elif odoo_field_type in ('date', 'datetime'):
                        odoo_field_value = question_val.split('+')[0].replace('T', ' ')
                    elif odoo_field_type == 'selection':
                        # TODO: Check if question_val is a valid selection!
                        odoo_field_value = question_val
                except Exception as e:
                    logger.error("Could not convert facebook question data to valid odoo field data! %s" % repr(e))

            # Add the data to the values
            if odoo_field_name and odoo_field_value:
                vals.update({odoo_field_name: odoo_field_value})
            else:
                vals['description'] += question_fb_field_key + ': ' + question_val + '\n'
