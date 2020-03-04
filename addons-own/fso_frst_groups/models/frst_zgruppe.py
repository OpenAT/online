# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


# Fundraising Studio group folders
# zGruppe are "folders" for groups that determine for what model a zGruppeDetail is valid
class FRSTzGruppe(models.Model):
    """
    zGruppe (frst.zgruppe) are like "Folders" for the real groups (= zGruppeDetail).
    These "folders" will set the "tabellentyp_id" or in other words the "model" that the "groups" inside of this
    folder are valid for!
    """
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

    gruppe_kurz = fields.Char(string="GruppeKurz", required=True,
                              help="Interne Bezeichnung")
    gruppe_lang = fields.Char(string="GruppeLang", required=True,
                              help="Anzeige fuer den Kunden und im GUI")
    gui_anzeigen = fields.Boolean("GuiAnzeigen")

    zgruppedetail_ids = fields.One2many(comodel_name="frst.zgruppedetail", inverse_name='zgruppe_id',
                                        string="zGruppeDetail IDS")

    ja_gui_anzeige = fields.Char(string="JaGuiAnzeige", required=True,
                                 help="Display text for 'yes'")

    nein_gui_anzeige = fields.Char(string="NeinGuiAnzeige", required=True,
                                   help="Display text for 'no'")
