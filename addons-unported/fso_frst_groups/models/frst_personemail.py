# -*- coding: utf-8 -*-
from openerp import models, fields, api


class FRSTPersonEmail(models.Model):
    _inherit = "frst.personemail"

    personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='frst_personemail_id',
                                            string="FRST PersonEmailGruppe IDS")

    # @api.model
    # def create(self, vals):
    #     context = self.env.context or {}
    #
    #     res = super(FRSTPersonEmail, self).with_context(
    #         skipp_update_main_personemail_id_and_checkboxes=True).create(vals)
    #
    #     if res and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners = res.mapped('partner_id')
    #         partners.update_main_personemail_id_and_checkboxes()
    #     return res
    #
    # @api.multi
    # def write(self, vals):
    #     context = self.env.context or {}
    #
    #     res = super(FRSTPersonEmail, self).with_context(
    #         skipp_update_main_personemail_id_and_checkboxes=True).write(vals)
    #
    #     if self and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners = self.mapped('partner_id')
    #         partners.update_main_personemail_id_and_checkboxes()
    #     return res
    #
    # @api.multi
    # def unlink(self):
    #     context = self.env.context or {}
    #     partners = False
    #     if self and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners = self.mapped('partner_id')
    #
    #     res = super(FRSTPersonEmail, self).with_context(
    #         skipp_update_main_personemail_id_and_checkboxes=True).unlink()
    #
    #     if partners and 'skipp_update_main_personemail_id_and_checkboxes' not in context:
    #         partners.update_main_personemail_id_and_checkboxes()
    #     return res
