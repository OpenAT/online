# -*- coding: utf-8 -*-
from openerp import models, fields


class FRSTPersonEmail(models.Model):
    _inherit = "frst.personemail"

    personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='frst_personemail_id',
                                            string="FRST PersonEmailGruppe IDS")
