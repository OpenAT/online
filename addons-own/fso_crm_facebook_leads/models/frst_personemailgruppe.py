# -*- coding: utf-8 -*-
from openerp import models, fields, api
import logging
logger = logging.getLogger(__name__)


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _inherit = "frst.personemailgruppe"

    crm_lead_ids = fields.One2many(string="CRM Leads",
                                   comodel_name="crm.lead", inverse_name="personemailgruppe_id",
                                   readonly=True,
                                   help="Used for crm.leads created by facebook lead imports")

    additional_crm_lead_ids = fields.Many2many(string="Additional CRM Leads",
                                               comodel_name="crm.lead",
                                               inverse_name="additional_subscription_ids",
                                               readonly=True,
                                               help="Used for crm.leads created by facebook lead imports from "
                                                    "consent checkboxes")

    # ATTENTION: This field will be set on Facebook lead import (crm.lead creation) and
    #            on install and update of this addon. It is basically a computed field.
    fb_form_id = fields.Many2one(string='Facebook Form ID', comodel_name='crm.facebook.form',
                                 readonly=True, ondelete='set null')

    @api.model
    def update_fb_form_id(self):
        """ This is just a helper function to compute the fb_form_id in case something went wrong! """
        logger.info('Recomputing field fb_form_id for frst.personemailgruppe records!')

        # Get all Forms with leads
        fb_forms = self.env['crm.facebook.form'].search([('crm_lead_ids', '!=', False)])
        logger.info("Found %s facebook form(s) with leads" % len(fb_forms))

        for form in fb_forms:
            # Search for related personemailgruppe with wrong fb_form_id
            pegs = form.crm_lead_ids.mapped('personemailgruppe_id')
            logger.info('Facebook form %s has %s personemailgruppe for %s leads'
                        '' % (form.id, len(pegs), len(form.crm_lead_ids)))
            wrong_pegs = pegs.filtered(lambda r: not r.fb_form_id or r.fb_form_id.id != form.id)
            if wrong_pegs:
                logger.warning("Found %s personemailgruppe with wrong fb_form_id!" % len(wrong_pegs))
                wrong_pegs.write({'fb_form_id': form.id})
