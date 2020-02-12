# -*- coding: utf-8 -*-

from openerp import api, models, fields
import requests
from facebook_graph_api import facebook_graph_api_url

import logging
logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    fb_lead_id = fields.Char('Facebook Lead ID', readonly=True)
    crm_form_id = fields.Many2one('crm.facebook.form', string='Form', ondelete='set null', readonly=True)
    crm_page_id = fields.Many2one('crm.facebook.page', string='Page',
                                  related='crm_form_id.crm_page_id', store=True,
                                  ondelete='set null', readonly=True)

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(fb_lead_id)', 'This Facebook lead already exists!')
    ]

    @api.model
    def get_facebook_leads(self):
        # TODO: Add status "error" to forms and a new field "activated" (Datetime) that will be set when the state
        #       changes from to_review to active and cleared when the state changes to 'to_review' or to 'error'

        # Get all active forms
        crm_forms_active = self.env['crm.facebook.form'].search([('state', '=', 'active')])
        logger.info("Import facebook leads for %s active forms" % len(crm_forms_active))

        for crm_form in crm_forms_active:

            # List of facebook lead ids of already imported leads
            imported_fb_lead_ids = crm_form.crm_lead_ids.mapped('fb_lead_id')

            # Get leads data from facebook for this form
            # TODO: Pagination
            fb_request_url = facebook_graph_api_url + crm_form.fb_form_id + "/leads"
            leads = requests.get(fb_request_url, params={'access_token': crm_form.fb_page_access_token}).json()
            if not leads.get('data'):
                logger.warning("Received no leads data for form with ID %s" % crm_form.id)
                continue
            logger.info('Got %s leads from facebook' % len(leads))

            # Only import new leads
            new_leads = [l for l in leads['data'] if l['id'] not in imported_fb_lead_ids]
            logger.info('Importing %s new leads from facebook' % len(new_leads))

            # Convert the facebook lead data to crm.leads records
            for lead in new_leads:

                crm_lead_values = crm_form.facebook_data_to_lead_data(lead)




        # OLD STUFF --------
        # Loop through all configured facebook pages
        for page in self.env['crm.facebook.page'].search([]):
            forms = self.env['crm.facebook.form'].search([('crm_page_id', '=', page.id),
                                                          ('state', '=', 'active')])
            for form in forms:
                r = requests.get(facebook_graph_api_url + form.fb_form_id + "/leads",
                                 params={'access_token': form.fb_page_access_token}).json()
                if r.get('data'):
                    for lead in r['data']:
                        if not self.search([('fb_lead_id', '=', lead.get('id')), '|', ('active', '=', True),
                                            ('active', '=', False)]):
                            vals = {}
                            notes = []
                            for field_data in lead['field_data']:
                                if field_data['name'] in form.mappings.filtered(
                                        lambda m: m.crm_field.id).mapped('fb_field_key'):
                                    crm_field = form.mappings.filtered(
                                        lambda m: m.fb_field_key == field_data['name']).crm_field
                                    if crm_field.ttype == 'many2one':
                                        related_value = self.env[crm_field.relation].search(
                                            [('display_name', '=', field_data['values'][0])])
                                        vals.update({crm_field.name: related_value and related_value.id})
                                    elif crm_field.ttype in ('float', 'monetary'):
                                        vals.update({crm_field.name: float(field_data['values'][0])})
                                    elif crm_field.ttype == 'integer':
                                        vals.update({crm_field.name: int(field_data['values'][0])})
                                    elif crm_field.ttype in ('date', 'datetime'):
                                        vals.update(
                                            {crm_field.name: field_data['values'][0].split('+')[0].replace('T', ' ')})
                                    elif crm_field.ttype == 'selection':
                                        vals.update({crm_field.name: field_data['values'][0]})
                                    else:
                                        vals.update({crm_field.name: ", ".join(field_data['values'])})
                                else:
                                    notes.append(field_data['name'] + ": " + ", ".join(field_data['values']))
                            if not vals.get('name'):
                                vals.update({'name': form.name + " - " + lead['id']})
                            vals.update({
                                'fb_lead_id': lead['id'],
                                'description': "\n".join(notes),
                                'section_id': form.section_id and form.section_id.id,
                                'campaign_id': form.campaign_id and form.campaign_id.id,
                                'source_id': form.source_id and form.source_id.id,
                                'medium_id': form.medium_id and form.medium_id.id,
                                'crm_page_id': page.id,
                                'crm_form_id': form.id,
                                'date_open': lead['created_time'].split('+')[0].replace('T', ' ')
                            })
                            lead = self.create(vals)
