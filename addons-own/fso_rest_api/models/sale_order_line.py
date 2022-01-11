# -*- coding: utf-8 -*-
from openerp import api, models


import logging
logger = logging.getLogger(__name__)


class SaleOrderLineRestAPI(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def write(self, values):
        # Access rights should not be handled in write method. This is a dirty hack, to
        # enforce API users can only update their own payment.transactions, no matter what.
        if self.env.user.has_group('fso_rest_api.frst_api_group'):
            logger.info("Write to sale.order.line from an API user: enforcing update own only")
            for record in self:
                assert self.env.user.id == record.create_uid.id

        res = super(SaleOrderLineRestAPI, self).write(values)
        return res
