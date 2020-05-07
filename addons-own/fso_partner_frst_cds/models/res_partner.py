# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    frst_zverzeichnis_id = fields.Many2one(string="CDS Origin",
                                           comodel_name='frst.zverzeichnis', inverse_name="partner_ids",
                                           domain=[('verzeichnistyp_id', '=', False)],
                                           readonly=True, ondelete='set null', index=True,
                                           track_visibility='onchange',
                                           help="Ursprungsaktion / zMarketingID / Herkunft",)
