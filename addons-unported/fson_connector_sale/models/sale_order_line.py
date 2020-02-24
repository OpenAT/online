# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderLineFSONConnectorSale(models.Model):
    _name = "sale.order.line"
    _inherit = "sale.order.line"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="sale_order_line_id")
