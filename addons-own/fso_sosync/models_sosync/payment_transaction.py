# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class PaymentTransactionSosync(models.Model):
    _name = "payment.transaction"
    _inherit = ["payment.transaction", "base.sosync"]

    _sync_job_priority = 4000

    # ------------------------------------------
    # COMMON FIELDS FOR ALL PAYMENT TRANSACTIONS
    # ------------------------------------------
    state = fields.Selection(sosync="fson-to-frst")
    state_message = fields.Text(sosync="fson-to-frst")

    date_create = fields.Datetime(sosync="fson-to-frst")
    date_validate = fields.Datetime(sosync="fson-to-frst")

    # acquirer_id = fields.Many2one(sosync="fson-to-frst")
    acquirer_reference = fields.Char(sosync="fson-to-frst")     # Reference of the TX as stored in the acquirer database
    # reference = fields.Char(sosync="fson-to-frst")
    # sale_order_id = fields.Many2one(sosync="fson-to-frst")

    amount = fields.Float(sosync="fson-to-frst")
    # fees = fields.Float(sosync="fson-to-frst")
    # currency_id = fields.Many2one(sosync="fson-to-frst")

    # ------------------------
    # ACQUIRER SPECIFIC FIELDS
    # ------------------------

    # payment_postfinance
    # -------------------
    esr_reference_number = fields.Char(sosync="fson-to-frst")

    # payment_frst
    # ------------
    frst_iban = fields.Char(sosync="fson-to-frst")
    frst_bic = fields.Char(sosync="fson-to-frst")

    # payment_consale
    # ---------------
    consale_provider_name = fields.Char(sosync="fson-to-frst")

    consale_method = fields.Selection(sosync="fson-to-frst")
    consale_method_other = fields.Char(sosync="fson-to-frst")
    consale_method_brand = fields.Char(sosync="fson-to-frst")

    consale_method_banktransfer_provider = fields.Selection(sosync="fson-to-frst")

    consale_method_account_owner = fields.Char(sosync="fson-to-frst")
    consale_method_account_iban = fields.Char(sosync="fson-to-frst")
    consale_method_account_bic = fields.Char(sosync="fson-to-frst")
    consale_method_account_bank = fields.Char(sosync="fson-to-frst")

    consale_recurring_payment_provider = fields.Selection(sosync="fson-to-frst")

    consale_error_code = fields.Char(sosync="fson-to-frst")
    consale_error_msg = fields.Char(sosync="fson-to-frst")

