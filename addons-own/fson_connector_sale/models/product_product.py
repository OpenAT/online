# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductProductFSONConnectorSale(models.Model):
    _name = "product.product"
    _inherit = "product.product"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="product_id")
