# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderFSONConnectorSale(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="sale_order_id")
