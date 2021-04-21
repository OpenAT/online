# -*- coding: utf-8 -*-

from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Add additional fields
    # HINT: 'partner_' fields are for the company! 'contact_' fields for the person in crm.lead
    #       but this seem sonly true for the name :( ... phone is even defined twice in crm.lead :(
    # ATTENTION: firstname and lastname fields are covered by the OCA addon 'crm_lead_firstname'
    contact_street_number_web = fields.Char(string='Street Number Web')
    contact_anrede_individuell = fields.Char(string='Individuelle Anrede')
    contact_title_web = fields.Char(string='Title Web')
    contact_birthdate_web = fields.Date(string='Birthdate Web')
    contact_newsletter_web = fields.Boolean(string='Newsletter Web')

    @api.model
    def _lead_create_contact(self, lead, name, is_company, parent_id=False):
        partner_id = super(CrmLead, self)._lead_create_contact(lead, name, is_company, parent_id)

        if not is_company and partner_id:
            logger.info("Add fields from addon fso_crm_extra_fields to the partner created from the lead!")
            partner = self.env["res.partner"].browse(partner_id)

            # Write fields with values first
            # ATTENTION: This was copied from 'crm_lead_firstname' but there .update() was used instead of .write() ?!?
            partner.write({
                'street_number_web': lead.contact_street_number_web,
                'anrede_individuell': lead.contact_anrede_individuell,
                'title_web': lead.contact_title_web,
                'birthdate_web': lead.contact_birthdate_web,
                'newsletter_web': lead.contact_newsletter_web,
            })

        return partner_id
