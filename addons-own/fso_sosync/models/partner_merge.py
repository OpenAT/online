# -*- coding: utf-'8' "-*-"
from openerp import api, models

import logging
logger = logging.getLogger(__name__)


class PartnerMerge(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner"]

    @api.model
    def merge_partner(self, partner_to_remove_id=False, partner_to_keep_id=False):
        # Log Info
        partner = self.env['res.partner']
        partner_to_remove = partner.browse([partner_to_remove_id])
        partner_to_keep = partner.browse([partner_to_keep_id])
        logger.info("merge_partner: Merge Partner %s (ID %s) into partner %s (ID %s)" %
                    (partner_to_remove.name, partner_to_remove_id, partner_to_keep.name, partner_to_keep_id))

        # Create an instance from the wizard to be able to use it's methods
        logger.info("merge_partner: create wizard")
        wizard = self.env['base.partner.merge.automatic.wizard']

        # Call the merge function of the wizard in old style api :)
        logger.info("merge_partner: call _merge()")
        #res = wizard._merge(wizard.env.cr, wizard.env.user.id, set([partner_to_keep_id, partner_to_remove_id]),
        #                    dst_partner=partner_to_keep, context=wizard.env.context)

        res = wizard._merge(set([partner_to_keep_id, partner_to_remove_id]), dst_partner=partner_to_keep,
                            context={})

        logger.info("merge_partner: return result: %s" % res)
        return res or False
