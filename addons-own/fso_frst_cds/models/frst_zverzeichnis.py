# -*- coding: utf-8 -*-
from openerp import models, fields, api
<<<<<<< HEAD
from openerp.exceptions import ValidationError
=======
>>>>>>> o8
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


# Fundraising Studio group folders
# zGruppe are "folders" for groups that determine for what model a zGruppeDetail is valid
class FRSTzVerzeichnis(models.Model):
    _name = "frst.zverzeichnis"
    _inherit = ['mail.thread']
    _rec_name = "verzeichnisname"

<<<<<<< HEAD
    verzeichnisname = fields.Char(string="Name", required=True, help="VerzeichnisName", track_visibility='onchange')
=======
    verzeichnisname = fields.Char(string="Name", help="VerzeichnisName", track_visibility='onchange')
>>>>>>> o8
    verzeichnislang = fields.Char(string="Beschreibung", help="VerzeichnisLang")
    verzeichniskuerzel = fields.Char(string="Kuerzel", help="Kuerzel HINT: Not used in most instances")
    bemerkung = fields.Text(string="Bemerkung", help="Bemerkung")

<<<<<<< HEAD
    parent_id = fields.Many2one(comodel_name="frst.zverzeichnis", inverse_name='child_ids', string="Ordner",
                                domain="[('verzeichnistyp_id','=',True)]",
                                help="zVerzeichnisIDParent, Folder in which this CDS record belongs",
                                track_visibility='onchange')
    child_ids = fields.One2many(comodel_name='frst.zverzeichnis', inverse_name='parent_id', string="Child IDS")

    verzeichnistyp_id = fields.Boolean(string="Ist ein Ordner",
                                       help="VerzeichnistypID, If set this is a folder",
                                       track_visibility='onchange')
    bezeichnungstyp_id = fields.Selection(string="Typ", selection=[('KA', 'Kampagne'),
                                                                   ('Aktion', 'Aktion'),
                                                                   ('ZG', 'Zielgruppe')],
=======
    parent_id = fields.Many2one(comodel_name="frst.zverzeichnis", inverse_name='child_ids', string="Parent",
                                help="zVerzeichnisIDParent, If True this is a CDS folder (and not a CDS file)",
                                track_visibility='onchange')
    child_ids = fields.One2many(comodel_name='frst.zverzeichnis', inverse_name='parent_id', string="Child IDS")

    verzeichnistyp_id = fields.Boolean(string="Ist ein Ordner", help="VerzeichnistypID", track_visibility='onchange')
    bezeichnungstyp_id = fields.Selection(string="Typ", selection=[('kampagne', 'Kampagne'),
                                                                   ('aktion', 'Aktion'),
                                                                   ('zielgruppe', 'Zielgruppe')],
>>>>>>> o8
                                          help="CDS Ordner sollten immer Aktion oder Kampagne sein, CDS Files "
                                               "sollten immer Zielgruppe sein",
                                          track_visibility='onchange')

    anlagedatum = fields.Date(string="Anlagedatum", required=True,
                              help="Anlagedatum HINT: Copy 'create_date' on "
                                   "record-creation-in-odoo to this field",
                              default=lambda s: fields.Datetime.now())

    # HINT: Has no effect on the selectable CDS records for 'anmeldelisten'
    startdatum = fields.Date(string="Startdatum", required=True,
                             help="Startdatum", track_visibility='onchange',
                             default=lambda s: fields.Datetime.now())
    endedatum = fields.Date(string="Endedatum", required=True,
                            help="Endedatum", track_visibility='onchange',
                            default=lambda s: fields.date(2099, 12, 31))

    # Not in use for 'anmeldelisten' (mail.mass_mailing.list)
    verantwortlicher_benutzer = fields.Char(string="Verantw. Benutzer", readonly=True,
                                            help="VerantwortlichBenutzer")
    fibukontonummer = fields.Char(string="FibuKontonummer", readonly=True, help="FibuKontonummer")
<<<<<<< HEAD
    cdsdokument = fields.Char(string="CDSDokument", readonly=True, help="CDSDokument")
    xbankverbindungidfuereinzugsvertraege = fields.Integer(string="xBankverbindungIDFuerEinzugsvertraege", readonly=True,
                                                          help="xBankverbindungIDFuerEinzugsvertraege")

    # DEPRECATED
    uebersteigendebeitraegeprojahraufspendenzverzeichnisid = fields.Integer(
        string="UebersteigendeBeitraegeproJahraufSpendenzVerzeichnisID", readonly=True,
        help="DEPRECATED UebersteigendeBeitraegeproJahraufSpendenzVerzeichnisID")
=======
    uebersteigendebeitraegeprojahraufspendenzverzeichnisid = fields.Integer(
        string="ÜbersteigendeBeiträgeproJahraufSpendenzVerzeichnisID", readonly=True,
        help="DEPRECATED ÜbersteigendeBeiträgeproJahraufSpendenzVerzeichnisID")
    cdsdokument = fields.Char(string="CDSDokument", readonly=True, help="CDSDokument")
    xbankverbindungidfuereinzugsvertraege = fields.Integer(string="xBankverbindungIDFürEinzugsverträge", readonly=True,
                                                          help="xBankverbindungIDFürEinzugsverträge")

    # DEPRECATED
>>>>>>> o8
    verwendungalszmarketingid = fields.Boolean(string="VerwendungAlszMarketingID", readonly=True,
                                               help="DEPRECATED LAUT PETRA VerwendungAlszMarketingID")
    sorterinhierarchie = fields.Integer(string="SorterinHierarchie", readonly=True,
                                        help='DEPRECATED LAUT SEBI SorterinHierarchie')
    organisationseinheit = fields.Char(string="Organisationseinheit", readonly=True,
                                       help=" DEPRACTED LAUT PETRA Organisationseinheit")

    @api.constrains("parent_id", "verzeichnistyp_id")
    def constraint_parent_id(self):
        for r in self:
<<<<<<< HEAD
            # REGEL: Nicht "file auf file" und nicht "ordner auf file"
=======
            # REGEL: Nicht file auf file und nicht ordner auf file
>>>>>>> o8
            if r.parent_id:
                # Only link to parent folders
                assert r.parent_id.verzeichnistyp_id, _(
                    "You can only move CDS files and CDS folder into CDS folders (but not into CDS files)!")

<<<<<<< HEAD
    @api.multi
    def unlink(self):

        # ATTENTION: We do not know if there are any records related to this CDS record in FRST.
        #            Therefore only the sosyncer (=FRST) can delete a CDS record but not any user in FSON!
        if not self.env.user.has_group('base.sosync'):
            raise ValidationError('You can not delete CDS records directly in FS-Online!\n'
                                  'Please delete them in Fundraising Studio!')

        return super(FRSTzVerzeichnis, self).unlink()
=======

    # TODO: Prevent deletion in odoo ?!?
>>>>>>> o8
