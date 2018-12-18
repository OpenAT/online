# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentTransactionSosync(models.Model):
    _name = "payment.transaction"
    _inherit = ["payment.transaction", "base.sosync"]

    state = fields.Selection(sosync="True")
    frst_iban = fields.Char(sosync="True")
    frst_bic = fields.Char(sosync="True")
    acquirer_reference = fields.Char(sosync="True")
    esr_reference_number = fields.Char(sosync="True")
    reference = fields.Char(sosync="True")
