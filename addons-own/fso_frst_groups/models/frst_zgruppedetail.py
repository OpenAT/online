# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
import logging
logger = logging.getLogger(__name__)


# Fundraising Studio groups
class FRSTzGruppeDetail(models.Model):
    _name = "frst.zgruppedetail"
    _rec_name = "gruppe_lang"

    # Compute a name based on <frst_id> - <zgruppe_id.tabelentyp_id> - <gruppe_lang>
    # display_name = fields.Char(string="Group Name",
    #                            compute="_compute_display_name",
    #                            search="_search_display_name",
    #                            readonly=True,
    #                            store=False)

    zgruppe_id = fields.Many2one(comodel_name="frst.zgruppe", inverse_name='zgruppedetail_ids',
                                 string="Gruppenordner",
                                 required=True, ondelete="cascade", index=True)

    tabellentyp_id = fields.Selection(related="zgruppe_id.tabellentyp_id", readonly=True, store=True)

    geltungsbereich = fields.Selection(string="Geltungsbereich",
                                       selection=[('local', 'Local Group'),
                                                  ('system', 'System Group')],
                                       default='system')
    gui_anzeige_profil = fields.Boolean(string="GuiAnzeigeProfil",
                                        help="Show this group in the person profile view.",
                                        default=True)

    gruppe_kurz = fields.Char(string="GruppeKurz", required=True,
                              help="gruppe_kurz is no longer in use - use gruppe_lang instead! "
                                   "The value of gruppe_lang will be copied to gruppe_kurz if gruppe_kurz is empty!")
    gruppe_lang = fields.Char(string="GruppeLang", required=True)
    gui_anzeigen = fields.Boolean("GuiAnzeigen",
                                  help="If set this group is available for this instance")
    active = fields.Boolean(string="Active", compute="_compute_active", store=True)

    # ATTENTION: "gueltig_von" und "gueltig_bis" is NOT IN USE for zGruppeDetail and may be removed in the future!
    #
    #            But these fields ARE IN USE by the specific groups-for-models models like "frst.persongruppe"!
    #            The fields are inherited through the abstract class "frst.gruppestate"
    #
    gueltig_von = fields.Date(string="GueltigVon", required=True,
                              default=lambda s: fields.Datetime.now())   # Not used -> Wird in Sicht integriert als Anlagedatum. Ist derzeit nicht als Anlagedatum gedacht!
    gueltig_bis = fields.Date(string="GueltigBis", required=True,
                              default=lambda s: fields.date(2099, 12, 31))   # Not used

    # PersonGruppe
    frst_persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='zgruppedetail_id',
                                            string="PersonGruppe IDS")
    frst_persongruppe_count = fields.Integer(string="Person Subscribers",
                                             compute="cmp_frst_persongruppe_count")

    # PersonEmailGruppe
    frst_personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='zgruppedetail_id',
                                                 string="PersonEmailGruppe IDS")
    frst_personemailgruppe_count = fields.Integer(string="E-Mail Subscribers",
                                                  compute="cmp_frst_personemailgruppe_count")

    # NEW SETTING FOR GROUPS / CHECKBOXES THAT MUST BE VALIDATE BY BY SOME SORT OF APPROVAL
    # HINT: This field is checked on group creation in abstract class frst.gruppestate > create()
    # approval_needed = fields.Boolean("Approval needed",
    #                                  default=False,
    #                                  help="If this checkbox is set gueltig_von and gueltig_bis will be set to "
    #                                       "the past date 09.09.1999 when the group is created to indicate that "
    #                                       "an approval is needed before set the group to active.")

    bestaetigung_erforderlich = fields.Boolean(string="Approval needed",
                                               default=False,
                                               help="If this checkbox is set gueltig_von and gueltig_bis will be set "
                                                    "to the past date 09.09.1999 when the group is created to indicate "
                                                    "that an approval is needed before set the group to active.")
    bestaetigung_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn'),
                                                   ('phone_call', "Phone Call"),
                                                   ('workflow', "Fundraising Studio Workflow"),
                                                   ],
                                        string="Approval Type", default='doubleoptin')

    # @api.multi
    # @api.depends('gruppe_lang', 'zgruppe_id')
    # def _compute_display_name(self):
    #     tabellentyp_dict = dict(self.env['frst.zgruppe']._fields['tabellentyp_id'].selection)
    #     for r in self:
    #         r.display_name = "%s (%s, %s)" % (
    #             r.gruppe_lang or r.gruppe_kurz,
    #             tabellentyp_dict.get(r.zgruppe_id.tabellentyp_id, _('unknown')).upper() if r.zgruppe_id else _('unknown'),
    #             r.sosync_fs_id if 'sosync_fs_id' in r._fields else _('unknown')
    #         )

    @api.depends('gui_anzeigen')
    def _compute_active(self):
        for r in self:
            r.active = r.gui_anzeigen

    def _search_display_name(self, operator, value):
        return ['|',
                  ('gruppe_lang', operator, value),
                  ('sosync_fs_id', operator, value)
                ]

    @api.onchange('gruppe_lang', 'geltungsbereich')
    def onchange_gruppe_lang_geltungsbereich(self):
        for r in self:
            if r.gruppe_lang and not r.gruppe_kurz:
                r.gruppe_kurz = r.gruppe_lang
            if r.geltungsbereich == 'local':
                r.gui_anzeigen = True

    @api.multi
    def cmp_frst_persongruppe_count(self):
        for r in self:
            r.frst_persongruppe_count = len(self.frst_persongruppe_ids) or 0

    @api.multi
    def cmp_frst_personemailgruppe_count(self):
        for r in self:
            r.frst_personemailgruppe_count = len(self.frst_personemailgruppe_ids) or 0

    @api.model
    def create(self, vals):
        if vals.get('geltungsbereich') != 'local':
            assert self.env.user.has_group('base.sosync'), _("You can not create a system group!")

        return super(FRSTzGruppeDetail, self).create(vals)

    @api.multi
    def write(self, vals):
        if self and vals and not self.env.user.has_group('base.sosync'):
            # Do not change the group folder (because of the tabellentyp_id)
            if 'zgruppe_id' in vals:
                raise ValidationError(_("You can not change the group folder (zgruppe_id). Please delete and "
                                        "recreate the group!"))
            # Do not change the "geltungsbereich"
            if 'geltungsbereich' in vals:
                raise ValidationError(_("You can not change the 'geltungsbereich'. Please delete and "
                                        "recreate the group!"))

            # Prevent the change of any relevant fields for system groups
            if any(r.geltungsbereich != 'local' for r in self):
                if any(f in vals for f in ['zgruppe_id', 'geltungsbereich', 'gui_anzeige_profil', 'gruppe_kurz',
                                           'gruppe_lang', 'gui_anzeigen', 'gueltig_von', 'gueltig_bis', 'steuerung_bit',
                                           ]):
                    raise ValidationError('You can not change system groups!')

        return super(FRSTzGruppeDetail, self).write(vals)

    @api.multi
    def unlink(self):
        if not self.env.user.has_group('base.sosync'):
            if any(r.geltungsbereich != 'local' for r in self):
                raise ValidationError('You can not delete system groups!')

        return super(FRSTzGruppeDetail, self).unlink()
