# -*- coding: utf-8 -*-
from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class FRSTzVerzeichnis(models.Model):
    _inherit = "frst.zverzeichnis"

    frst_zgruppedetail_ids = fields.One2many(string="FRST Groups",
                                             comodel_name='frst.zgruppedetail',
                                             inverse_name='frst_zverzeichnis_id',
                                             readonly=True)

    frst_personemailgruppe_ids = fields.One2many(string="FRST Groups",
                                                 comodel_name='frst.personemailgruppe',
                                                 inverse_name='frst_zverzeichnis_id',
                                                 readonly=True)

    frst_persongruppe_ids = fields.One2many(string="FRST Groups",
                                            comodel_name='frst.persongruppe',
                                            inverse_name='frst_zverzeichnis_id',
                                            readonly=True)
