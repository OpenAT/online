# -*- coding: utf-'8' "-*-"
import logging

from openerp.osv import orm

_logger = logging.getLogger(__name__)


class PaymentTransaction(orm.Model):
    _inherit = 'payment.transaction'

    def form_feedback(self, cr, uid, data, acquirer_name, context=None):
        res = super(PaymentTransaction, self).form_feedback(cr, uid, data, acquirer_name, context=context)
        _logger.info("Kucken wie des ableitet !!!")
        return res
