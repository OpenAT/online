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

    gruppe_kurz = fields.Char("GruppeKurz", required=True)
    gruppe_lang = fields.Char("GruppeLang", required=True)
    gui_anzeigen = fields.Boolean("GuiAnzeigen",
                                  help="If set this group is available for this instance")

    # ATTENTION: gueltig_von und gueltig_bis is NOT IN USE for zGruppeDetail and can be removed in the future
    gueltig_von = fields.Date("GueltigVon", required=True)   # Not used -> Wird in Sicht integriert als Anlagedatum. Ist derzeit nicht als Anlagedatum gedacht!
    gueltig_bis = fields.Date("GueltigBis", required=True)   # Not used

    # PersonGruppe
    frst_persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='zgruppedetail_id',
                                            string="PersonGruppe IDS")

    # PersonEmailGruppe
    frst_personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='zgruppedetail_id',
                                                 string="PersonEmailGruppe IDS")

