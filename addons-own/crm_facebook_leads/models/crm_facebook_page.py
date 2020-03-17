# -*- coding: utf-8 -*-

from openerp import api, models, fields
from static_data import facebook_graph_api_url
import requests

import logging

logger = logging.getLogger(__name__)


class CrmFacebookPage(models.Model):
    _name = 'crm.facebook.page'
    _inherit = ['mail.thread']

    name = fields.Char(required=True, string="Facebook Page Name")
    fb_page_id = fields.Char(required=True, string="Facebook Page ID")
    fb_page_access_token = fields.Char(required=True, string='Page Access Token')
    crm_form_ids = fields.One2many('crm.facebook.form', 'crm_page_id', string='Lead Forms')

    # SQL CONSTRAINTS
    _sql_constraints = [
        ('fb_fb_page_id', 'unique(fb_page_id)', 'Facebook page id must be unique')
    ]

    @api.multi
    def import_facebook_forms(self):
        crm_facebook_form_obj = self.env['crm.facebook.form']

        for r in self:
            facebook_forms = requests.get(facebook_graph_api_url + self.fb_page_id + "/leadgen_forms",
                                          params={'access_token': self.fb_page_access_token}).json()
            for fb_form in facebook_forms['data']:
                # HINT: Search for inactive forms too, so archived forms are not created over and over again
                crm_form_rec = crm_facebook_form_obj.search([('fb_form_id', '=', fb_form['id']),
                                                             '|', ('active', '=', True), ('active', '=', False)])
                if not crm_form_rec:
                    crm_facebook_form_obj.create({
                        'name': fb_form.get('name') or fb_form['id'],
                        'fb_form_id': fb_form['id'],
                        'fb_form_locale': fb_form.get('locale'),
                        'fb_form_status': fb_form.get('status'),
                        'crm_page_id': r.id,
                    }).import_facebook_lead_fields()
                else:
                    if fb_form['status'].lower() != 'active':
                        crm_form_rec.write({'active': False})

    @api.multi
    def write(self, vals):
        res = super(CrmFacebookPage, self).write(vals)

        # Recompute the state of all existing forms if the page access token field gets changed!
        if res and 'fb_page_access_token' in vals:
            for r in self:
                if r.crm_form_ids:
                    r.crm_form_ids.compute_state()

        return res
