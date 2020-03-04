# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTzGruppeSosync(models.Model):
    _name = "frst.zgruppe"
    _inherit = ["frst.zgruppe", "base.sosync"]

    tabellentyp_id = fields.Selection(sosync="True")
    gruppe_kurz = fields.Char(sosync="True")
    gruppe_lang = fields.Char(sosync="True")
    gui_anzeigen = fields.Boolean(sosync="True")
    ja_gui_anzeige = fields.Char(sosync="True")
    nein_gui_anzeige = fields.Char(sosync="True")
