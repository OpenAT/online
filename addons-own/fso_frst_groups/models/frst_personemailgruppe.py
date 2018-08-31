# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _name = "frst.personemailgruppe"
    _inherit = ["frst.gruppestate"]

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_personemailgruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       required=True, ondelete='cascade')
    frst_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='personemailgruppe_ids',
                                          string="FRST PersonEmail",
                                          required=True, ondelete='cascade')
