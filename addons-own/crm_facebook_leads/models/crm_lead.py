# -*- coding: utf-8 -*-

from openerp import api, models, fields
import requests
from static_data import facebook_graph_api_url

import logging
logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    fb_lead_id = fields.Char('Facebook Lead ID', readonly=True, track_visibility='onchange')
    crm_form_id = fields.Many2one('crm.facebook.form', string='Form',
                                  ondelete='set null', readonly=True, index=True, track_visibility='onchange')
    crm_page_id = fields.Many2one('crm.facebook.page', string='Page',
                                  related='crm_form_id.crm_page_id', store=True,
                                  ondelete='set null', readonly=True, index=True)

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(fb_lead_id)', 'This Facebook lead already exists!')
    ]

    @api.model
    def import_facebook_leads(self):
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
            new_leads = [ld for ld in leads['data'] if ld['id'] not in imported_fb_lead_ids]
            logger.info('Importing %s new leads from facebook' % len(new_leads))

            # Convert the facebook lead data to crm.leads records
            for lead in new_leads:
                crm_lead_values = crm_form.facebook_data_to_lead_data(lead)
                crm_lead = self.create(crm_lead_values)
                if crm_lead:
                    logger.info("Facebook lead (fb_lead_id: %s) successfully imported as crm.lead %s)"
                                "" % (crm_lead.fb_lead_id, crm_lead.id))
                else:
                    logger.error("Crm lead import failed!")
