# -*- coding: utf-8 -*-
from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # zVerzeichnis field to copy the setting from the form at creation time to the crm.lead!
    # HINT: Copy this from fbform -> zgruppedetail to crm.lead at lead creation: Done in facebook_data_to_lead_data()
    frst_zverzeichnis_id = fields.Many2one(string="CDS Origin",
                                           comodel_name="frst.zverzeichnis", inverse_name='crm_lead_ids',
                                           domain=[('verzeichnistyp_id', '=', False)],
                                           readonly=True, ondelete='set null', index=True,
                                           track_visibility='onchange',
                                           help="Ursprungsaktion / Herkunft / zMarketingID \n"
                                                "Fundraising Studio CDS List/File. "
                                                "This will be copied at lead creation from the setting of the "
                                                "zGruppeDetail set in the facebook lead form")

    # If a facebook leads creates a FRST Group Subscription we link the subscription to the crm.lead
    personemailgruppe_id = fields.Many2one(string="PersonEmailGruppe",
                                           comodel_name='frst.personemailgruppe', inverse_name="crm_lead_ids",
                                           readonly=True, ondelete='set null', index=True,
                                           track_visibility='onchange')

    @api.model
    def create(self, vals):
        lead = super(CrmLead, self).create(vals)

        # SPECIAL HANDLING FOR CRM.LEADS THAT REPRESENTS IMPORTED FACEBOOK LEADS
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

            # Create a FRST group subscription ("PersonEmailGruppe") if set in the form
            if lead.crm_form_id.zgruppedetail_id:
                p_personemail = lead.partner_id.main_personemail_id
                lead_email = lead.email_from

                if not p_personemail:
                    logger.error("The person (id %s) created by the facebook lead has no main email! "
                                 "Could not create the group Subscription!" % lead.partner_id.id)
                elif p_personemail.email.strip().lower() != lead_email.strip().lower():
                    logger.error("The main email of the partner (id %s) is not matching the facebook lead! "
                                 "Could not create the group Subscription!" % lead.partner_id.id)
                else:
                    # TODO: Check if the double opt in set in the group leads to the state 'approval needed'!
                    # TODO: Check if the lead is correctly linked to the PersonEmailGruppe
                    peg_vals = {
                        'zgruppedetail_id': lead.crm_form_id.zgruppedetail_id.id,
                        'frst_personemail_id': p_personemail.id,
                        'frst_zverzeichnis_id': lead.frst_zverzeichnis_id.id if lead.frst_zverzeichnis_id else False,
                        'crm_lead_ids': [(4, lead.id, False)],
                        'fb_form_id': lead.crm_form_id.id
                    }
                    peg = self.env['frst.personemailgruppe'].create(peg_vals)
                    logger.info("Created subscription (PersonEmailGruppe (id %s)) for facebook crm.lead (id %s)"
                                "" % (peg.id, lead.id))

        return lead

    @api.model
    def _lead_create_contact(self, lead, name, is_company, parent_id=False):
        """Add default_frst_zverzeichnis_id (CDS Ursprungsaktion) to the partner created from the lead."""
        partner_id = super(CrmLead, self)._lead_create_contact(lead, name, is_company, parent_id)

        if partner_id and lead.frst_zverzeichnis_id:
            logger.info("Add frst_zverzeichnis_id to the partner created from the lead!")
            partner = self.env["res.partner"].browse(partner_id)

            # Write fields with values first
            # ATTENTION: This was copied from 'crm_lead_firstname' but there .update() was used instead of .write() ?!?
            partner.write({
                'frst_zverzeichnis_id': lead.frst_zverzeichnis_id.id,
            })

        return partner_id
