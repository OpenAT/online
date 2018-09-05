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

    # Main e-mail groups (related field)
    main_email_personemailgruppe_ids = fields.One2many(related='main_personemail_id.personemailgruppe_ids',
                                                       string="Main Email Groups", readonly=True)

    # @api.model
    # def create(self, vals):
    #     res = super(ResPartner, self).create(vals)
    #
    #     if 'main_personemail_id' in vals:
    #         res.group_to_checkbox()
    #
    #     return res
    #
    # @api.multi
    # def write(self, vals):
    #     res = super(ResPartner, self).write(vals)
    #
    #     if 'main_personemail_id' in vals:
    #         self.group_to_checkbox()
    #
    #     return res

    @api.model
    def create(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(ResPartner, self).create(values)

        # Checkboxes to groups for all bridge models
        if 'skipp_checkbox_to_group' not in context:
            res.checkbox_to_group(values)

        # Update checkboxes by groups if main email changes for frst.personemail bridge model
        if 'main_personemail_id' in values:
            res.group_to_checkbox()

        return res

    @api.multi
    def write(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(ResPartner, self).write(values)

        # Checkboxes to groups
        if 'skipp_checkbox_to_group' not in context:
            self.checkbox_to_group(values)

        # Update checkboxes by groups if main email changes for frst.personemail bridge model
        if 'main_personemail_id' in values:
            self.group_to_checkbox()

        return res
