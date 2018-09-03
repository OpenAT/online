# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "frst.checkboxmodel"]

    _bridge_model_fields = ('persongruppe_ids',)

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='partner_id',
                                       string="FRST PersonGruppe IDS")
