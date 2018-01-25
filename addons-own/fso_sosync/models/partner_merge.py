# -*- coding: utf-'8' "-*-"
from openerp import api, models
from openerp.exceptions import ValidationError
from openerp.tools import SUPERUSER_ID

import logging
logger = logging.getLogger(__name__)


class PartnerMerge(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner"]

    @api.noguess
    def _merge_partner(self, cr, uid, partner_to_remove, partner_to_keep, context={}):
        # Create an instance from the wizard to be able to use it's methods
        logger.info("merge_partner: Create a base.partner.merge.automatic.wizard instance")
        wizard = self.pool.get('base.partner.merge.automatic.wizard')

        # MERGE PARTNER
        # -------------
        # Update foreign keys directly in the db
        logger.info("merge_partner: Update foreign keys directly in the db")
        wizard._update_foreign_keys(cr, SUPERUSER_ID, partner_to_remove, partner_to_keep, context=context)

        # Update reference fields
        logger.info("merge_partner: Update reference fields")
        wizard._update_reference_fields(cr, SUPERUSER_ID, partner_to_remove, partner_to_keep, context=context)

        # Update target partner field values
        # ATTENTION: DISABLED because the field values will be already corrected in FRST!
        #logger.info("merge_partner: Update field values")
        #wizard._update_values(cr, SUPERUSER_ID, partner_to_remove, partner_to_keep, context=context)

    @api.model
    def merge_partner(self, partner_to_remove_id=False, partner_to_keep_id=False):
        cr = self.env.cr
        uid = self.env.uid
        context = self.env.context or {}
        # HINT: There is also an OCA module base_partner_merge which seems to be exactly the same than the code in
        #       the crm addon. maybe odoo just copied the code or the oca extracted it because the addon crm was the
        #       wrong place for it?

        # Load partner and log info
        # HINT: This will throw an exception if any of the partners do not exits
        partner = self.env['res.partner']

        partner_to_remove = partner.browse([partner_to_remove_id])
        assert partner_to_remove, "merge_partner: partner_to_remove (ID %s) was not found!" % partner_to_remove_id

        partner_to_keep = partner.browse([partner_to_keep_id])
        assert partner_to_keep, "merge_partner: partner_to_keep (ID %s) was not found!" % partner_to_keep_id

        logger.info("merge_partner: Merge Partner %s (ID %s) into partner %s (ID %s)" %
                    (partner_to_remove.name, partner_to_remove_id, partner_to_keep.name, partner_to_keep_id))

        # Check if the partner_to_remove is a child of the partner_to_keep
        if partner_to_remove.parent_id and partner_to_remove.parent_id.id == partner_to_keep.id:
            raise ValidationError("You cannot merge a contact with his parent!")

        # Check if the partner_to_remove has account journal items
        if self.env['ir.model'].sudo().search([('model', '=', 'account.move.line')]):
            if self.env['account.move.line'].sudo().search([('partner_id', '=', partner_to_remove.id)]):
                raise ValidationError("You cannot merge a contact with account journal entries!")

        # MERGE
        # -----
        # HINT: Done in a separate method to avoid new to old api mapping with decorator @api.noguess because
        #       the automatic mapping failed for the wizard methods called in _merge_partner()
        logger.debug("merge_partner: Call _merge_partner()")
        self._merge_partner(cr, uid, partner_to_remove, partner_to_keep, context=context)
        # Post a message to the partner_to_keep chatter flow
        partner_to_keep.message_post(body="Partner %s (ID %s) was merged into this partner!"
                                          % (partner_to_remove.name, partner_to_remove_id))

        # UNLINK
        # ------
        # Remove the merged partner
        logger.info("merge_partner: Unlink (delete) the partner_to_remove (ID %s) after the merge"
                    % partner_to_remove_id)
        partner_to_remove.unlink()

        # EMPTY WRITE
        # -----------
        logger.info("merge_partner: Do an empty write({}) for the remaining partner %s to update all state information"
                    "" % partner_to_keep_id)
        partner_to_keep.write({})

        logger.info("merge_partner: DONE: Merged Partner with id %s into partner with id %s!"
                    % (partner_to_remove_id, partner_to_keep_id))
        return True
