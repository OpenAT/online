# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class SaleOrderLineSosync(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "base.sosync"]

    _sync_job_priority = 4000

    # This model is read-only in FRST

    order_id = fields.Many2one(sosync="fson-to-frst")
    product_id = fields.Many2one(sosync="fson-to-frst")
    payment_interval_id = fields.Many2one(sosync="fson-to-frst")
    price_donate = fields.Float(sosync="fson-to-frst")

    # Price per item (price_donate will be copied to this field!)
    price_unit = fields.Float(sosync="fson-to-frst")

    # Number of items
    product_uos_qty = fields.Float(sosync="fson-to-frst")

    state = fields.Selection(sosync="fson-to-frst")
    fs_ptoken = fields.Char(sosync="fson-to-frst")
    fs_origin = fields.Char(sosync="fson-to-frst")

    # Copied from the product to the sale.order.line to avoid changes after sale order confirmation
    # WARNING: We assume here that zgruppedetail are NEVER deleted!
    zgruppedetail_ids = fields.Many2many(sosync="fson-to-frst")

    # fs_product_type is now also copied by _cart_update() to the so line
    # ATTENTION: in product.template fs_product_type is a selection field but in so line for convenience only a char
    fs_product_type = fields.Char(sosync="fson-to-frst")
