# -*- coding: utf-8 -*-
from openerp import models, fields, api
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "frst.checkboxmodel"]

    _bridge_model_fields = ('persongruppe_ids', 'main_email_personemailgruppe_ids')

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='partner_id',
                                       track_visibility='onchange',
                                       string="FRST PersonGruppe IDS")

    # Main e-mail groups (related field)
    main_email_personemailgruppe_ids = fields.One2many(related='main_personemail_id.personemailgruppe_ids',
                                                       track_visibility='onchange',
                                                       string="Main Email Groups", readonly=True)

    @api.model
    def create(self, values):
        values = values or {}
        context = self.env.context or {}

        res = super(ResPartner, self).create(values)

        # Checkboxes to groups for all bridge models
        if 'skipp_checkbox_to_group' not in context:
            res.checkbox_to_group(values)

        return res

    @api.multi
    def write(self, values):
        values = values or {}
        context = self.env.context or {}

        # if 'email' in values:
        #     email_only = {'email': values.pop('email')}
        #     res = super(ResPartner, self).write(email_only)

        res = super(ResPartner, self).write(values)

        # Checkboxes to groups
        if 'skipp_checkbox_to_group' not in context:
            self.checkbox_to_group(values)

        # Update checkboxes by groups if main email changes for frst.personemail bridge model
        if 'main_personemail_id' in values:
            self.group_to_checkbox()

        return res
