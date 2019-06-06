# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderLineSosync(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "base.sosync"]

    order_id = fields.Many2one(sosync="True")
    product_id = fields.Many2one(sosync="True")
    payment_interval_id = fields.Many2one(sosync="True")
    price_donate = fields.Float(sosync="True")

    # Price per item (price_donate will be copied to this field!)
    price_unit = fields.Float(sosync="True")

    # Number of items
    product_uos_qty = fields.Float(sosync="True")

    state = fields.Selection(sosync="True")
    fs_ptoken = fields.Char(sosync="True")
    fs_origin = fields.Char(sosync="True")

    # Copied from the product to the sale.order.line to avoid changes after sale order confirmation
    # WARNING: We assume here that zgruppedetail are NEVER deleted!
    zgruppedetail_ids = fields.Many2many(sosync="True")

    # fs_product_type is now also copied by _cart_update() to the so line
    # ATTENTION: in product.template fs_product_type is a selection field but in so line for convenience only a char
    fs_product_type = fields.Char(sosync="True")
