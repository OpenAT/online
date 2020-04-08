# -*- coding: utf-8 -*-
from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class FRSTzGruppeDetail(models.Model):
    _inherit = "frst.zgruppedetail"

    crm_fb_form_ids = fields.One2many(string="Facebook Lead Forms",
                                      comodel_name="crm.facebook.form", inverse_name='zgruppedetail_id',
                                      readonly=True,
                                      help="Facebook Leads Forms that may use this group in the crm.lead "
                                           "creation process")
