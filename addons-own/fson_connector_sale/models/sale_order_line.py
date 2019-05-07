# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderLineAltruja(models.Model):
    _name = "sale.order.line"
    _inherit = "sale.order.line"

    altruja_ids = fields.One2many(comodel_name="altruja", inverse_name="sale_order_line_id")
