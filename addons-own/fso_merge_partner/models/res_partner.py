# -*- coding: utf-8 -*-
from openerp import models, api
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class ResPartnerFSOMerge(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "fso.merge"]

    # ---------
    # FSO MERGE
    # ---------
    @api.model
    def _fso_merge_validate(self, rec_to_remove=None, rec_to_keep=None):
        res = super(ResPartnerFSOMerge, self)._fso_merge_validate(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        logger.info("FSO MERGE FOR res.partner: _fso_merge_validate() that the partner-to-remove is not a child or "
                    "parent of the partner-to-keep!")

        children_of_rec_to_keep = self.search([('id', 'child_of', [rec_to_keep.id])])
        if rec_to_remove.id in children_of_rec_to_keep.ids:
            raise ValidationError("You cannot merge a partner with his parent!")

        children_of_rec_to_remove = self.search([('id', 'child_of', [rec_to_remove.id])])
        if rec_to_keep.id in children_of_rec_to_remove.ids:
            raise ValidationError("You cannot merge a partner with his child!")

        logger.info("FSO MERGE FOR res.partner: _fso_merge_validate() that the partner-to-remove has no "
                    "accounting records!")

        if self.env['ir.model'].sudo().search([('model', '=', 'account.move.line')]):
            if self.env['account.move.line'].sudo().search([('partner_id', '=', rec_to_remove.id)]):
                raise ValidationError("You cannot merge a partner with existing account journal entries!")

        return res

    @api.model
    def _fso_merge_pre(self, rec_to_remove=None, rec_to_keep=None):
        res = super(ResPartnerFSOMerge, self)._fso_merge_pre(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        # Merge the res.user of partner-to-remove before we merge the partners
        users_rec_to_remove = self.env['res.users'].search([('partner_id', '=', rec_to_remove.id)])
        assert len(users_rec_to_remove) <= 1, "More than one res.user (ids: %s) found for the partner-to-remove!" \
                                              "" % users_rec_to_remove.ids
        users_rec_to_keep = self.env['res.users'].search([('partner_id', '=', rec_to_keep.id)])
        assert len(users_rec_to_remove) <= 1, "More than one res.user (ids: %s) found for the partner-to-keep!" \
                                              "" % users_rec_to_keep.ids
        if len(users_rec_to_remove) == 1 and len(users_rec_to_keep) == 1:
            logger.info("Merge res.user of partner-to-remove into res.user of partner-to-keep pre merge!")
            self.env['res.users'].fso_merge(remove_id=users_rec_to_remove.id,
                                            keep_id=users_rec_to_keep.id)

        return res
