# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentAcquirerFSONConnectorSale(models.Model):
    _name = "payment.acquirer"
    _inherit = "payment.acquirer"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="acquirer_id")
