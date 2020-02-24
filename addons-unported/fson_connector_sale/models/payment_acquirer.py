# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentAcquirerFSONConnectorSale(models.Model):
    _name = "payment.acquirer"
    _inherit = "payment.acquirer"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="acquirer_id")

    # Enable for fson_connector_sale
    fson_connector_sale = fields.Boolean(string="Enabled in Connector Sale",
                                         help="Enable in fson_connector_sale")
