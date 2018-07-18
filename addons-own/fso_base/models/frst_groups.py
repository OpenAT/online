# -*- coding: utf-8 -*-
from openerp import models, fields


# Fundraising Studio group folders
# zGruppe are "folders" for groups that determine for what model a zGruppeDetail is valid
class FRSTzGruppe(models.Model):
    _name = "frst.zgruppe"
    _rec_name = "gruppe_lang"

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
                                      help="Select model where Groups in this folder apply",
                                      required=True)

    gruppe_kurz = fields.Char("GruppeKurz", required=True,
                              help="Interne Bezeichnung")
    gruppe_lang = fields.Char("GruppeLang", required=True,
                              help="Anzeige fuer den Kunden und im GUI")
    gui_anzeigen = fields.Boolean("GuiAnzeigen")

    zgruppedetail_ids = fields.One2many(comodel_name="frst.zgruppedetail", inverse_name='zgruppe_id',
                                        string="zGruppeDetail IDS")


# Fundraising Studio groups
class FRSTzGruppeDetail(models.Model):
    _name = "frst.zgruppedetail"
    _rec_name = "gruppe_lang"

    zgruppe_id = fields.Many2one(comodel_name="frst.zgruppe", inverse_name='zgruppedetail_ids',
                                 string="zGruppeID",
                                 required=True)

    gruppe_kurz = fields.Char("GruppeKurz", required=True)
    gruppe_lang = fields.Char("GruppeLang", required=True)
    gui_anzeigen = fields.Boolean("GuiAnzeigen",
                                  help="If set this group is available for this instance")

    gueltig_von = fields.Date("GültigVon", required=True)   # Not used -> Wird in Sicht integriert als Anlagedatum. Ist derzeit nicht als Anlagedatum gedacht!
    gueltig_bis = fields.Date("GültigBis", required=True)   # Not used

    # PersonGruppe
    frst_persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='zgruppedetail_id',
                                            string="PersonGruppe IDS")

    # PersonEmailGruppe
    frst_personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='zgruppedetail_id',
                                                 string="PersonEmailGruppe IDS")


# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _name = "frst.persongruppe"

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_persongruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100100')],
                                       required=True)
    partner_id = fields.Many2one(comodel_name="res.partner", inverse_name='persongruppe_ids',
                                string="Person",
                                required=True)
    steuerung_bit = fields.Boolean(string="Steuerung Bit")
    gueltig_von = fields.Date("GültigVon", required=True)
    gueltig_bis = fields.Date("GültigBis", required=True)


# Inverse Field for PersonGruppe
class ResPartner(models.Model):
    _inherit = 'res.partner'

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='partner_id',
                                       string="FRST PersonGruppe IDS")


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _name = "frst.personemailgruppe"

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_personemailgruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       required=True)
    frst_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='personemailgruppe_ids',
                                          string="FRST PersonEmail",
                                          required=True, ondelete='cascade')
    steuerung_bit = fields.Boolean(string="Steuerung Bit")
    gueltig_von = fields.Date("GültigVon", required=True)
    gueltig_bis = fields.Date("GültigBis", required=True)


# Inverse Field for PersonEmailGruppe
class FRSTPersonEmail(models.Model):
    _inherit = "frst.personemail"

    personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='frst_personemail_id',
                                            string="FRST PersonEmailGruppe IDS")
