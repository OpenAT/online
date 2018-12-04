# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductPaymentIntervalSosync(models.Model):
    _name = "product.payment_interval"
    _inherit = ["product.payment_interval", "base.sosync"]

    name = fields.Text(sosync="True")
