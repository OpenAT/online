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

