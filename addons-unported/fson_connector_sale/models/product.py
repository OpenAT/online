# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductProductFSONConnectorSale(models.Model):
    _name = "product.product"
    _inherit = "product.product"

    fson_connector_sale_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="product_id")


class ProductTemplateFSONConnectorSale(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    # Enable for fson_connector_sale
    fson_connector_sale = fields.Boolean(string="Enabled in Connector Sale",
                                         help="Enable in fson_connector_sale")
