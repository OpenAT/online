# -*- coding: utf-'8' "-*-"
from openerp import models, fields,api


class SaleOrderLineWebsiteSaleDonate(models.Model):
    _inherit = "sale.order.line"

    price_subtotal_stored = fields.Float(compute="cmp_price_subtotal_stored",
                                         store=True, readonly=True)

    @api.depends('price_unit', 'product_id', 'tax_id', 'discount', 'order_id', 'product_uom_qty')
    def cmp_price_subtotal_stored(self):
        for r in self:
            r.price_subtotal_stored = r.price_subtotal
