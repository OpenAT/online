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

        logger.info("FSO MERGE FOR res.partner: _fso_merge_validate() that the partner-to-remove is not a child of the "
                    "partner-to-keep!")
        if rec_to_remove.parent_id and rec_to_remove.parent_id.id == rec_to_keep.id:
            raise ValidationError("You cannot merge a partner with his parent!")

        logger.info("FSO MERGE FOR res.partner: _fso_merge_validate() that the partner-to-remove has no "
                    "accounting records!")
        # Check if the partner_to_remove has account journal items
        if self.env['ir.model'].sudo().search([('model', '=', 'account.move.line')]):
            if self.env['account.move.line'].sudo().search([('partner_id', '=', rec_to_remove.id)]):
                raise ValidationError("You cannot merge a partner with existing account journal entries!")

        return res

    # TODO: Write tests and check what happens for res.user!!!
