# -*- coding: utf-8 -*-

from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    fb_lead_id = fields.Char('Facebook Lead ID', readonly=True, track_visibility='onchange')
    crm_form_id = fields.Many2one('crm.facebook.form', string='Form',
                                  readonly=True, track_visibility='onchange')
    crm_page_id = fields.Many2one('crm.facebook.page', string='Page',
                                  related='crm_form_id.crm_page_id', store=True,
                                  readonly=True,)

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(fb_lead_id)', 'This Facebook lead already exists!')
    ]
