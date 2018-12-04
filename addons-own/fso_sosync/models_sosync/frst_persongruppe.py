# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTPersonGruppeSosync(models.Model):
    _name = "frst.persongruppe"
    _inherit = ["frst.persongruppe", "base.sosync"]

    zgruppedetail_id = fields.Many2one(sosync="True")
    partner_id = fields.Many2one(sosync="True")
    steuerung_bit = fields.Boolean(sosync="True")
    gueltig_von = fields.Date(sosync="True")
    gueltig_bis = fields.Date(sosync="True")
