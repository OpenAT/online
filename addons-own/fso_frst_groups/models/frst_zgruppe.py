# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import ValidationError

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

    gruppe_kurz = fields.Char(string="GruppeKurz", required=True, help="Interne Bezeichnung")
    gruppe_lang = fields.Char(string="GruppeLang", required=True, help="Anzeige fuer den Kunden und im GUI")
    gui_anzeigen = fields.Boolean(string="GuiAnzeigen")
    active = fields.Boolean(string="Active", compute="_compute_active", store=True)

    zgruppedetail_ids = fields.One2many(comodel_name="frst.zgruppedetail", inverse_name='zgruppe_id',
                                        string="zGruppeDetail IDS")

    ja_gui_anzeige = fields.Char(string="JaGuiAnzeige", required=True,
                                 default="not_yet_synced_odoo_default",
                                 help="Display text for 'yes'")

    nein_gui_anzeige = fields.Char(string="NeinGuiAnzeige", required=True,
                                   default="not_yet_synced_odoo_default",
                                   help="Display text for 'no'")

    geltungsbereich = fields.Selection(string="Geltungsbereich",
                                       selection=[('local', 'Local Group'),
                                                  ('system', 'System Group')],
                                       default='system')

    gui_gruppen_bearbeiten_moeglich = fields.Boolean(
        string="Bearbeitung durch Sachbearbeiter",
        default=True,
        readonly=True,
        help="Wenn nicht gesetzt, können Gruppenzuweisungen für Gruppen in diesem Gruppenordner nicht von "
             "Sachbearbeitern zugewiesen, entfernt oder geändert werden.")

    nur_eine_gruppe_anmelden = fields.Boolean(
        string="Exklusive Gruppenanmeldung",
        default=False,
        readonly=True,
        help="Wenn gesetzt kann nur eine Gruppe des Gruppenordners zugeordnet werden. Wird eine andere Gruppe aus dem"
             "Ordner zugeordnet wird die vorangegangene Gruppenzuordnung gelöscht.")

    # ATTENTION: Diese Felder sind nur in FRST vorhanden und werden beim FSRT-Merge beruecksichtigt:
    #
    # TODO: Nur eine zGruppeDetail im Gruppenordner darf einem Datensatz zugeordnet werden (z.B. Person)
    # TODO: Mehrfache Zuweisung der selben zGruppeDetail im Gruppenordner auf einen Datensatz ist nicht erlaubt
    #       Beispiel einer Mehrfachzuordnung: kommt nur für Statistikgruppen vor die auch ablaufen koennen
    #       z.B.: 'Großpender' im Jahr 2018 aber nicht 2019 dann wieder 2020
    #       ACHTUNG: Der default Wert ist 'True' da im Regelfall eine mehrfache Zuordnung nicht sinnig ist
    # TODO: Nur eine zGruppeDetail im Gruppenordner darf gueltig sein
    #       INFO: Ist nur sinnhaft für 'Status' oder 'Statistikgruppen' z.B.: 'Daten sind aktuell', 'inaktiv', ...

    @api.depends('gui_anzeigen')
    def _compute_active(self):
        for r in self:
            r.active = r.gui_anzeigen

    @api.model
    def create(self, vals):
        if vals.get('geltungsbereich') != 'local':
            assert self.env.user.has_group('base.sosync'), _("You can not create a system group folder!")

        return super(FRSTzGruppe, self).create(vals)

    @api.multi
    def write(self, vals):
        if self and vals and not self.env.user.has_group('base.sosync'):
            if any(r.geltungsbereich != 'local' for r in self):
                raise ValidationError('You can not change a system group folder')

        return super(FRSTzGruppe, self).write(vals)

    @api.multi
    def unlink(self):
        if not self.env.user.has_group('base.sosync'):
            if any(r.geltungsbereich != 'local' for r in self):
                raise ValidationError('You can not delete system group folders')

        return super(FRSTzGruppe, self).unlink()
