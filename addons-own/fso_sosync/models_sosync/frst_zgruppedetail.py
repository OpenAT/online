# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTzGruppeDetailSosync(models.Model):
    _name = "frst.zgruppedetail"
    _inherit = ["frst.zgruppedetail", "base.sosync"]

    zgruppe_id = fields.Many2one(sosync="True")
    frst_zverzeichnis_id = fields.Many2one(sosync="True")

    gruppe_kurz = fields.Char(sosync="True")
    gruppe_lang = fields.Char(sosync="True")
    gui_anzeigen = fields.Boolean(sosync="True")
    gueltig_von = fields.Date(sosync="True")
    gueltig_bis = fields.Date(sosync="True")

    subscription_email = fields.Many2one(sosync="True")             # Link an E-Mail template for the automatic Double-Opt-In e-mail. The Workflow is in FRST to send the e-mail and must be activated once!

    bestaetigung_erforderlich = fields.Boolean(sosync="True")
    bestaetigung_typ = fields.Selection(sosync="True")
    bestaetigung_email = fields.Many2one(sosync="True")
    bestaetigung_success_email = fields.Many2one(sosync="True")
    bestaetigung_text = fields.Char(sosync="True")
    bestaetigung_thanks = fields.Html(sosync="True")

    gui_anzeige_profil = fields.Boolean(sosync="True")

    geltungsbereich = fields.Selection(sosync="True")
