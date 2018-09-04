# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "frst.checkboxmodel"]

    _bridge_model_fields = ('persongruppe_ids', 'main_email_personemailgruppe_ids')

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='partner_id',
                                       string="FRST PersonGruppe IDS")

    main_email_personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe",
                                                       string="Main Email Groups", readonly=True,
                                                       compute="_compute_main_email_personemailgruppe_ids")

    @api.depends('frst_personemail_ids.main_address')
    def _compute_main_email_personemailgruppe_ids(self):
        for r in self:
            main_address = r.frst_personemail_ids.filtered(lambda m: m.main_address)
            if main_address:
                assert len(main_address) == 1, "More than one main e-mail address for partner %s" % r.id
            if not main_address:
                r.main_email_personemailgruppe_ids = False
            else:
                r.main_email_personemailgruppe_ids = main_address.personemailgruppe_ids
