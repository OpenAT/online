# -*- coding: utf-8 -*-

from openerp import api, models, fields
import requests
from static_data import facebook_graph_api_url

import logging
logger = logging.getLogger(__name__)


class CrmFacebookForm(models.Model):
    _name = 'crm.facebook.form'
    _inherit = ['mail.thread']

    name = fields.Char(required=True, readonly=True)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection(selection=[('to_review', 'To review'),
                                        ('active', 'Active'),
                                        ('error', 'Error'),
                                        ('archived', 'Archived')],
                             string='State', index=True, track_visibility='onchange',
                             compute='compute_state', store=True, readonly=True)
    activated = fields.Datetime(string='Approved/Activated at', readonly=True, track_visibility='onchange')

    fb_form_id = fields.Char(required=True, readonly=True, string='Form ID')
    crm_page_id = fields.Many2one(comodel_name='crm.facebook.page', string='Facebook Page',
                                  required=True, readonly=True, ondelete='cascade', index=True)
    mappings = fields.One2many(comodel_name='crm.facebook.form.field', inverse_name='crm_form_id',
                               track_visibility='onchange')

    # Sales team / leads section
    section_id = fields.Many2one(comodel_name='crm.case.section',
                                 domain=['|',
                                         ('use_leads', '=', True),
                                         ('use_opportunities', '=', True)],
                                 string="Sales Team")

    # UTM tracking
    campaign_id = fields.Many2one(comodel_name='utm.campaign', string='Campaign', index=True)
    source_id = fields.Many2one(comodel_name='utm.source', string='Source', index=True)
    medium_id = fields.Many2one(comodel_name='utm.medium', string='Medium', index=True)

    # Created crm.leads
    crm_lead_ids = fields.One2many(comodel_name='crm.lead', inverse_name='crm_form_id', readonly=True)

    # HINT: If the fb_page_access_token field is changed this method is triggered also!
    @api.depends('active', 'activated', 'crm_page_id', 'fb_form_id')
    def compute_state(self):
        for r in self:
            if not r.active:
                r.state = 'archived'
            elif not r.fb_form_id or not r.crm_page_id or not r.crm_page_id.fb_page_access_token:
                r.state = 'error'
            elif r.activated:
                r.state = 'active'
            else:
                r.state = 'to_review'

    @api.multi
    def button_activate(self):
        self.write({'activated': fields.datetime.now()})

    @api.multi
    def button_deactivate(self):
        self.write({'activated': False})

    @api.multi
    def button_archive(self):
        self.write({'active': False})

    @api.multi
    def button_unarchive(self):
        self.write({'active': True, 'activated': False})

    @api.multi
    def import_facebook_lead_fields(self):
        self.mappings.unlink()
        r = requests.get(facebook_graph_api_url + self.fb_form_id,
                         params={'access_token': self.crm_page_id.fb_page_access_token,
                                 'fields': 'questions'}).json()
        if r.get('questions'):
            for question in r.get('questions'):
                self.env['crm.facebook.form.field'].create({
                    'crm_form_id': self.id,
                    'fb_label': question['label'],
                    'fb_field_id': question['id'],
                    'fb_field_key': question['key'],
                    'fb_field_type': question.get('type', False)
                })

    @staticmethod
    def parse_date(string_val):
        # TODO: Eventually replace with date parsing library
        if '/' in string_val and 'T' not in string_val:
            us_date_parts = string_val.split('/')
            return us_date_parts[2] + '-' + us_date_parts[0] + '-' + us_date_parts[1]
        elif '/' in string_val and 'T' in string_val:
            us_date_all_parts = string_val.split('T')
            us_date_parts = us_date_all_parts[0].split('/')
            return us_date_parts[2] + '-' + us_date_parts[0] + '-' + us_date_parts[1] + ' ' + us_date_all_parts[1]
        else:
            return string_val.split('+')[0].replace('T', ' ')

    @api.multi
    def facebook_data_to_lead_data(self, facebook_lead_data=None):
        assert isinstance(facebook_lead_data, dict), "facebook_lead_data must be a dictionary!"
        self.ensure_one()
        crm_form = self

        # Basic crm.lead data
        date_open = fields.datetime.now()
        if facebook_lead_data.get('created_time'):
            try:
                date_open = facebook_lead_data['created_time'].split('+')[0].replace('T', ' ')
            except Exception as e:
                logger.error("Could not convert facebook lead create time! %s" % repr(e))
        vals = {
            'fb_lead_id': facebook_lead_data['id'],
            'date_open': date_open,
            'description': '',
            'section_id': crm_form.section_id and crm_form.section_id.id,
            'campaign_id': crm_form.campaign_id and crm_form.campaign_id.id,
            'source_id': crm_form.source_id and crm_form.source_id.id,
            'medium_id': crm_form.medium_id and crm_form.medium_id.id,
            'crm_page_id': crm_form.crm_page_id.id,
            'crm_form_id': crm_form.id,
        }

        # Loop through facebook form fields (questions)
        # TODO: Currently we only support facebook questions with a single answer/value
        for question in facebook_lead_data['field_data']:
            question_fb_field_key = question.get('name')
            question_val = question['values'][0]

            # Check if the facebook field is mapped to a crm.lead field
            crm_facebook_form_field = crm_form.mappings.filtered(lambda f: f.fb_field_key == question_fb_field_key)

            # Try to convert question data to valid odoo field data for mapped fields
            odoo_field_name = False
            odoo_field_value = False
            if crm_facebook_form_field:
                odoo_field = crm_facebook_form_field.crm_field
                odoo_field_name = odoo_field.name
                odoo_field_type = odoo_field.ttype
                try:
                    if odoo_field_type == 'many2one':
                        # TODO: !!! Handling for country_id and state_id !!!
                        rec = self.env[odoo_field.relation].search([('name', '=', question_val)], limit=1)
                        odoo_field_value = rec.id if rec else False
                    elif odoo_field_type in ('float', 'monetary'):
                        odoo_field_value = float(question_val)
                    elif odoo_field_type == 'integer':
                        odoo_field_value = int(question_val)
                    elif odoo_field_type in ('date', 'datetime'):
                        odoo_field_value = CrmFacebookForm.parse_date(question_val)
                    elif odoo_field_type == 'selection':
                        # TODO: Check if question_val is a valid selection value!
                        odoo_field_value = question_val
                    elif odoo_field_type in ('char', 'text'):
                        odoo_field_value = question_val
                except Exception as e:
                    logger.error("Could not convert facebook question data to valid odoo field data! %s" % repr(e))

            # Add the data to the values
            if odoo_field_name and odoo_field_value:
                vals.update({odoo_field_name: odoo_field_value})
            else:
                vals['description'] += question_fb_field_key + ': ' + question_val + '\n'

        # Always add the name field for the crm.lead
        if not vals.get('name'):
            if vals.get('partner_name'):
                vals['name'] = vals.get('partner_name')
            elif vals.get('firstname') or vals.get('lastname'):
                vals['name'] = (vals['firstname'] + ' ') if vals.get('firstname') else '' + vals.get('lastname', '')
            else:
                vals['name'] = 'facebook_lead_' + vals['fb_lead_id']

        # Return the values
        return vals

    def import_facebook_paginated_leads(self, crm_form, leads, imported_fb_lead_ids):
        logger.info('Got %s leads from facebook' % len(leads))

        # Only import new leads
        new_leads = [ld for ld in leads if ld['id'] not in imported_fb_lead_ids]
        logger.info('Importing %s new leads from facebook' % len(new_leads))

        # Convert the facebook lead data to crm.leads records
        for lead in new_leads:
            crm_lead_values = crm_form.facebook_data_to_lead_data(lead)
            crm_lead = self.env['crm.lead'].create(crm_lead_values)
            if crm_lead:
                logger.info("Facebook lead (fb_lead_id: %s) successfully imported as crm.lead %s)"
                            "" % (crm_lead.fb_lead_id, crm_lead.id))
            else:
                logger.error("Crm lead import failed!")

    @api.multi
    def import_facebook_leads(self):
        # Get all active forms if no specific forms are selected
        if not self:
            crm_forms_active = self.env['crm.facebook.form'].search([('state', '=', 'active')])
        else:
            crm_forms_active = self.filtered(lambda frm: frm.state == 'active')
        logger.info("Import facebook leads for %s active forms" % len(crm_forms_active))

        for crm_form in crm_forms_active:
            # List of facebook lead ids of already imported leads
            imported_fb_lead_ids = crm_form.crm_lead_ids.mapped('fb_lead_id')

            # Get leads data from facebook for this form
            fb_request_url = facebook_graph_api_url + crm_form.fb_form_id + "/leads"
            answer = requests.get(fb_request_url,
                                  params={'access_token': crm_form.crm_page_id.fb_page_access_token}).json()

            if not answer.get('data'):
                logger.warning("Received no leads data for form with ID %s" % crm_form.id)
                continue

            while answer.get('data'):
                self.import_facebook_paginated_leads(crm_form=crm_form,
                                                     leads=answer['data'],
                                                     imported_fb_lead_ids=imported_fb_lead_ids)

                # Request next page, if there is one, otherwise break the loop
                paging = answer['paging']
                if paging.get('next'):
                    answer = requests.get(paging['next']).json()
                else:
                    break

    # TODO: Avoid unlink() if crm.leads are linked to this form
