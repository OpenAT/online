# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTPersonEmailGruppeSosync(models.Model):
    _name = "frst.personemailgruppe"
    _inherit = ["frst.personemailgruppe", "base.sosync"]

    zgruppedetail_id = fields.Many2one(sosync="True")
    frst_personemail_id = fields.Many2one(sosync="True")
    steuerung_bit = fields.Boolean(sosync="True")
    gueltig_von = fields.Date(sosync="True")
    gueltig_bis = fields.Date(sosync="True")
