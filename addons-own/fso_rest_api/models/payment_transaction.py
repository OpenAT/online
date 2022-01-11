# -*- coding: utf-8 -*-
from openerp import api, models
from openerp.exceptions import ValidationError


import logging
logger = logging.getLogger(__name__)


class PaymentTransactionRestAPI(models.Model):
    _inherit = "payment.transaction"

    @api.multi
    def write(self, values):
        # Access rights should not be handled in write method. This is a dirty hack, to
        # enforce API users can only update their own payment.transactions, no matter what.
        if self.env.user.has_group('fso_rest_api.frst_api_group'):
            logger.info("Write to payment.transaction from an API user: enforcing update own only")
            for record in self:
                assert self.env.user.id == record.create_uid.id

        res = super(PaymentTransactionRestAPI, self).write(values)
        return res
