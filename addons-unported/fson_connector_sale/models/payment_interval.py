# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductPaymentIntervalFSONConnectorSale(models.Model):
    _name = "product.payment_interval"
    _inherit = "product.payment_interval"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="payment_interval_id")
