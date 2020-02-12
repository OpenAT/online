# -*- coding: utf-8 -*-

from openerp import api, models, fields
import requests
from facebook_graph_api import facebook_graph_api_url


class CrmFacebookForm(models.Model):
    _name = 'crm.facebook.form'

    name = fields.Char(required=True, readonly=True)
    fb_form_id = fields.Char(required=True, readonly=True, string='Form ID')
    fb_page_access_token = fields.Char(required=True, related='crm_page_id.fb_page_access_token', string='Page Access Token')
    crm_page_id = fields.Many2one('crm.facebook.page', readonly=True, ondelete='cascade', string='Facebook Page')
    mappings = fields.One2many('crm.facebook.form.field', 'crm_form_id')
    state = fields.Selection(selection=[('to_review', 'To review'),
                                        ('active', 'Active'),
                                        ('archived', 'Archived')],
                             string='State', required=True, index=True)
    active = fields.Boolean(default=True)

    # team_id does not exist in o8, use crm.case.section instead
    section_id = fields.Many2one('crm.case.section', domain=['|',
                                                             ('use_leads', '=', True),
                                                             ('use_opportunities', '=', True)],
                                 string="Sales Team")

    campaign_id = fields.Many2one('utm.campaign', string='Campaign')
    source_id = fields.Many2one('utm.source', string='Source')
    medium_id = fields.Many2one('utm.medium', string='Medium')

    @api.multi
    def get_fields(self):
        self.mappings.unlink()
        r = requests.get(facebook_graph_api_url + self.fb_form_id,
                         params={'access_token': self.fb_page_access_token, 'fields': 'questions'}).json()
        if r.get('questions'):
            for question in r.get('questions'):
                self.env['crm.facebook.form.field'].create({
                    'crm_form_id': self.id,
                    'label': question['label'],
                    'facebook_field_id': question['id'],
                    'facebook_field_key': question['key']
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
