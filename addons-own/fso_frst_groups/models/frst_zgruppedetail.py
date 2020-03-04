# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


# Fundraising Studio groups
class FRSTzGruppeDetail(models.Model):
    _name = "frst.zgruppedetail"
    _rec_name = "gruppe_lang"

    # TODO: Display name method (gruppe_kurz + gruppe_lang)

    zgruppe_id = fields.Many2one(comodel_name="frst.zgruppe", inverse_name='zgruppedetail_ids',
                                 string="zGruppeID",
                                 required=True, ondelete="cascade")

    gruppe_kurz = fields.Char(string="GruppeKurz", required=True)
    gruppe_lang = fields.Char(string="GruppeLang", required=True)
    gui_anzeigen = fields.Boolean("GuiAnzeigen",
                                  help="If set this group is available for this instance")

    # ATTENTION: "gueltig_von" und "gueltig_bis" is NOT IN USE for zGruppeDetail and may be removed in the future!
    #
    #            But these fields ARE IN USE by the specific groups-for-models models like "frst.persongruppe"!
    #            The fields are inherited through the abstract class "frst.gruppestate"
    #
    gueltig_von = fields.Date(string="GueltigVon", required=True)   # Not used -> Wird in Sicht integriert als Anlagedatum. Ist derzeit nicht als Anlagedatum gedacht!
    gueltig_bis = fields.Date(string="GueltigBis", required=True)   # Not used

    # PersonGruppe
    frst_persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='zgruppedetail_id',
                                            string="PersonGruppe IDS")

    # PersonEmailGruppe
    frst_personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='zgruppedetail_id',
                                                 string="PersonEmailGruppe IDS")

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
                                                   ],
                                        string="Approval Type", default='doubleoptin')

    gui_anzeige_profil = fields.Boolean(string="GuiAnzeigeProfil",
                                        help="Show this group in the person profile view.",
                                        default=True)
