# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentTransactionFSONConnectorSale(models.Model):
    _name = "payment.transaction"
    _inherit = "payment.transaction"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="payment_transaction_id")
