# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductPaymentIntervalSosync(models.Model):
    _name = "product.payment_interval"
    _inherit = ["product.payment_interval", "base.sosync"]

    # This model is read-only in FRST

    name = fields.Text(sosync="fson-to-frst")
    xml_id = fields.Char(sosync="fson-to-frst")     # unique name to be used by FRST to match the payment interval
