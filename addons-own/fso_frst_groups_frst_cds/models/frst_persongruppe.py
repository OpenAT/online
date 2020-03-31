# -*- coding: utf-8 -*-
from openerp import models, fields, api

import logging
logger = logging.getLogger(__name__)


# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _inherit = "frst.persongruppe"

    frst_zverzeichnis_id = fields.Many2one(string="CDS Origin",
                                           comodel_name='frst.zverzeichnis', inverse_name="frst_persongruppe_ids",
                                           domain=[('verzeichnistyp_id', '=', False)],
                                           readonly=True, ondelete='set null', index=True,
                                           help="Ursprungsaktion / zMarketingID / Herkunft",)
