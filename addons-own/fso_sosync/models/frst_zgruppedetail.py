# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTzGruppeDetailSosync(models.Model):
    _name = "frst.zgruppedetail"
    _inherit = ["frst.zgruppedetail", "base.sosync"]

    zgruppe_id = fields.Many2one(sosync="True")
    gruppe_kurz = fields.Char(sosync="True")
    gruppe_lang = fields.Char(sosync="True")
    gui_anzeigen = fields.Boolean(sosync="True")
    gueltig_von = fields.Date(sosync="True")
    gueltig_bis = fields.Date(sosync="True")
