# -*- coding: utf-8 -*-
from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class FRSTzGruppeDetail(models.Model):
    _inherit = "frst.zgruppedetail"

    frst_zverzeichnis_id = fields.Many2one(string="CDS File",
                                           comodel_name='frst.zverzeichnis', inverse_name="frst_zgruppedetail_ids",
                                           ondelete='set null',
                                           help="This is just a helper that may be used in the creation of FRST actions"
                                                " that may be created in Fundraising Studio because this group gets "
                                                "subscribed or the  subscription is changed (e.g. 'approved' or "
                                                "'OptOut'",)

