# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentTransactionAltruja(models.Model):
    _name = "payment.transaction"
    _inherit = "payment.transaction"

    altruja_ids = fields.One2many(comodel_name="altruja", inverse_name="payment_transaction_id")
