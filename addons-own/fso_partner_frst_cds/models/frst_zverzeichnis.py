# -*- coding: utf-8 -*-
from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class FRSTzVerzeichnis(models.Model):
    _inherit = "frst.zverzeichnis"

    partner_ids = fields.One2many(string="FRST Groups",
                                  comodel_name='res.partner', inverse_name='frst_zverzeichnis_id',
                                  readonly=True)
