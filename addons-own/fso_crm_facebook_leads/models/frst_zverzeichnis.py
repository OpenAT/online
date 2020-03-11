# -*- coding: utf-8 -*-
from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class FRSTzVerzeichnis(models.Model):
    _inherit = "frst.zverzeichnis"

    crm_fb_form_ids = fields.One2many(string="Facebook Lead Forms",
                                      comodel_name="crm.facebook.form", inverse_name='frst_zverzeichnis_id',
                                      readonly=True,
                                      help="Facebook Leads Forms that may use this CDS leave in the crm.lead "
                                           "creation process")

    crm_lead_ids = fields.One2many(string="Leads",
                                   comodel_name="crm.lead", inverse_name='frst_zverzeichnis_id',
                                   readonly=True,
                                   help="Facebook Leads Forms that may use this CDS leave in the crm.lead "
                                        "creation process")
