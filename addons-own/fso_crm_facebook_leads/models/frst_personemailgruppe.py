# -*- coding: utf-8 -*-
from openerp import models, fields
import logging
logger = logging.getLogger(__name__)


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _inherit = "frst.personemailgruppe"

    crm_lead_ids = fields.One2many(string="CRM Leads",
                                   comodel_name="crm.lead", inverse_name="personemailgruppe_id",
                                   readonly=True,
                                   help="Used for crm.leads created by facebook lead imports")

