# -*- coding: utf-8 -*-

from openerp import models, fields


class PaymentTransactionSosync(models.Model):
    _name = 'payment.transaction'
    _inherit = ['payment.transaction', 'base.sosync']

    consale_provider_name = fields.Char(sosync="fson-to-frst")
    consale_method = fields.Selection(sosync="fson-to-frst")
    consale_method_other = fields.Char(sosync="fson-to-frst")
    consale_method_brand = fields.Char(sosync="fson-to-frst")

    consale_method_directdebit_provider = fields.Selection(sosync="fson-to-frst")
    consale_method_account_owner = fields.Char(sosync="fson-to-frst")
    consale_method_account_iban = fields.Char(sosync="fson-to-frst")
    consale_method_account_bic = fields.Char(sosync="fson-to-frst")
    consale_method_account_bank = fields.Char(sosync="fson-to-frst")

    consale_recurring_payment_provider = fields.Selection(sosync="fson-to-frst")

    consale_error_code = fields.Char(sosync="fson-to-frst")
    consale_error_msg = fields.Char(sosync="fson-to-frst")
