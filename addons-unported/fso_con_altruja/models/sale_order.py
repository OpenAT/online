# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderAltruja(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    altruja_ids = fields.One2many(comodel_name="altruja", inverse_name="sale_order_id")
