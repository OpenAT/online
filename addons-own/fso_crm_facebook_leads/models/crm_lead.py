# -*- coding: utf-8 -*-
from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # TODO: Add a zVerzeichnis field to copy the setting from the form at creation time to the crm.lead!

    @api.model
    def create(self, vals):
        lead = super(CrmLead, self).create(vals)

        # Special handling for crm.leads that represents imported facebook leads
        if lead and lead.crm_form_id:

            # Convert the lead directly to an opportunity by wizard to create a new res.partner
            if lead.crm_form_id.force_create_partner and (not lead.type or lead.type == 'lead'):
                wizard_obj = self.env['crm.lead2opportunity.partner'].with_context(
                    active_model='crm.lead', active_id=lead.id, active_ids=lead.ids)

                wizard = wizard_obj.create({
                    'name': 'convert',
                    'action': 'create',
                    'opportunity_ids': False,
                    'partner_id': False,
                })

                wizard.action_apply()

            # TODO: Create a FRST group subscription ("PersonEmailGruppe") if set in the form

        return lead
