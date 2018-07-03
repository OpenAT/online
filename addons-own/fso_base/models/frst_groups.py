# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _


# Fundraising Studio group folders
# zGruppe are "folders" for groups that determine for what model a zGruppeDetail is valid
class FRSTzGruppe(models.Model):
    _name = "frst.zgruppe"

    tabellentyp_id = fields.Selection(selection=[('100100', 'Person'),
                                                 ('100102', 'Adresse'),
                                                 ('100104', 'Kommunikation'),
                                                 ('100106', 'Vertrag'),
                                                 ('100108', 'zVerzeichnis'),
                                                 ('100110', 'Email'),
                                                 ('100112', 'Telefon'),
                                                 ('100114', 'zEvent'),
                                                 ('100116', 'Aktion')],
                                      string="TabellentypID",
                                      help="Select model where Groups in this folder apply")

    gruppe_kurz = fields.Char("GruppeKurz")
    gruppe_lang = fields.Char("GruppeLang")
    gui_anzeigen = fields.Boolean("GuiAnzeigen")

    zgruppedetail_ids = fields.One2many(comodel_name="frst.zgruppedetail", inverse_name='zgruppe_id',
                                        string="zGruppeDetail IDS")


# Fundraising Studio groups
class FRSTzGruppeDetail(models.Model):
    _name = "frst.zgruppedetail"

    zgruppe_id = fields.Many2one(comodel_name="frst.zgruppe", inverse_name='zgruppedetail_ids',
                                 string="zGruppeID",
                                 required=True)

    gruppe_kurz = fields.Char("GruppeKurz")
    gruppe_lang = fields.Char("GruppeLang")
    gui_anzeigen = fields.Boolean("GuiAnzeigen")
    gueltig_von = fields.Date("GültigVon")
    gueltig_bis = fields.Date("GültigBis")

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='zgruppedetail_id',
                                       string="PersonGruppe IDS")


# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _name = "frst.persongruppe"

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='zgruppedetail_ids',
                                       string="zGruppeDetailID",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100100')],
                                       required=True)
    person_id = fields.Many2one(comodel_name="res.partner", inverse_name='persongruppe_ids',
                                string="Person",
                                required=True)
    steuerung_bit = fields.Selection(selection=[('1', 'Einschluss'), ('0', 'Ausschluss')])
    gueltig_von = fields.Date("GültigVon")
    gueltig_bis = fields.Date("GültigBis")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    zgruppedetail_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='person_id',
                                        string="zGruppeDetail IDS")
