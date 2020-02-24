# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerFSONConnectorSale(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    fson_connector_sale_partner_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="partner_id")
    fson_connector_sale_employee_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="employee_id")
    fson_connector_sale_donee_ids = fields.One2many(comodel_name="fson.connector.sale", inverse_name="donee_id")
