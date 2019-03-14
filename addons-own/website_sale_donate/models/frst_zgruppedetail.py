# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api


# Fundraising Studio groups
class FRSTzGruppeDetailWebsiteSaleDonate(models.Model):
    _inherit = "frst.zgruppedetail"

    product_template_ids = fields.Many2many(comodel_name='product.template', string='Product Templates')
    #product_product_ids = fields.Many2many(comodel_name='product.product', string='Product Templates')
    sale_order_line_ids = fields.Many2many(comodel_name='sale.order.line', string='Sale Order Lines')
