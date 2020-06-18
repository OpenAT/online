# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentTransactionSosync(models.Model):
    _name = "payment.transaction"
    _inherit = ["payment.transaction", "base.sosync"]

    _sync_job_priority = 4000

    # This model is read-only in FRST

    state = fields.Selection(sosync="fson-to-frst")
    frst_iban = fields.Char(sosync="fson-to-frst")
    frst_bic = fields.Char(sosync="fson-to-frst")
    acquirer_reference = fields.Char(sosync="fson-to-frst")
    esr_reference_number = fields.Char(sosync="fson-to-frst")
    reference = fields.Char(sosync="fson-to-frst")
    amount = fields.Float(sosync="fson-to-frst")
