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

    bestaetigung_erforderlich = fields.Boolean(sosync="True")
    bestaetigung_typ = fields.Selection(sosync="True")
    bestaetigung_email = fields.Many2one(sosync="True")
    bestaetigung_text = fields.Char(sosync="True")
    bestaetigung_thanks = fields.Html(sosync="True")

    gui_anzeige_profil = fields.Boolean(sosync="True")
