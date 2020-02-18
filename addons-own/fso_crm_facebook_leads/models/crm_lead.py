# -*- coding: utf-8 -*-

from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        lead = super(CrmLead, self).create(vals)

        # Convert the lead directly to an opportunity by wizard
        if lead and (not lead.type or lead.type == 'lead') \
                and lead.crm_form_id and lead.crm_form_id.force_create_partner:

            wizard_obj = self.env['crm.lead2opportunity.partner'].with_context(
                active_model='crm.lead', active_id=lead.id, active_ids=lead.ids)

            wizard = wizard_obj.create({
                'name': 'convert',
                'action': 'create',
                'opportunity_ids': False,
                'partner_id': False,
            })

            wizard.action_apply()

        return lead
