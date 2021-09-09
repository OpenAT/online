# -*- coding: utf-'8' "-*-"

import logging

from openerp import models, fields, api
from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class AcquirerConsale(models.Model):
    _inherit = 'payment.acquirer'

    @api.model
    def _get_providers(self):
        providers = super(AcquirerConsale, self)._get_providers()
        providers.append(['consale', 'Consale'])
        return providers

    @api.multi
    def consale_form_generate_values(self, partner_values, tx_values):
        self.ensure_one()

        # THIS SHOULD NOT BE NEEDED SINCE WE NEVER RENDER THE ACQUIRERE BUTTON
        # payment_consale is only used in fson_connector_sale right now

        return partner_values, tx_values

    @api.multi
    def consale_get_form_action_url(self):
        self.ensure_one()
        return '/payment/consale/feedback'


class PaymentTransactionConsale(models.Model):
    _inherit = 'payment.transaction'

    consale_state = fields.Selection(selection=[('draft', 'Draft'),
                                                ('pending', 'Pending'),
                                                ('done', 'Done'),
                                                ('error', 'Error'),
                                                ('cancel', 'Canceled')],
                                     string='State')
    consale_transaction_date = fields.Date(string='Payment Transaction Date')

    consale_provider_name = fields.Char(string='Payment Provider Name', help='e.g.: External Provider Name')
    consale_provider_status = fields.Char(string="Transaction Status Information")

    consale_method = fields.Selection(selection=[('paypal', 'PayPal'),
                                                 ('sofortueberweisung', 'Sofortüberweisung'),
                                                 ('applepay', 'Apple Pay'),
                                                 ('googlepay', 'Google Pay'),
                                                 ('banktransfer', 'Bank Transfer'),
                                                 ('creditcard', 'Credit Card'),
                                                 ('other', 'Other')],
                                      string='Payment Method')
    consale_method_other = fields.Char(string='"Other" Payment Method Name')
    consale_method_brand = fields.Char(string='Payment Method Brand', help="e.g.: Visa, Mastercard, Apple, ...")

    # For consale_method 'banktransfer'
    consale_method_banktransfer_provider = fields.Selection(string="Bank Transfer Payment Provider",
                                                            selection=[('frst', 'Fundraising Studio'),
                                                                       ('external', 'External Service')])
    consale_method_account_owner = fields.Char(string='Account Owner')
    consale_method_account_iban = fields.Char(string='Account IBAN')
    consale_method_account_bic = fields.Char(string='Account BIC')
    consale_method_account_bank = fields.Char(string='Account Bank Name')

    # For recurring payments
    consale_recurring_payment_provider = fields.Selection(string="Recurring Payment Provider",
                                                          selection=[('frst', 'Fundraising Studio'),
                                                                     ('external', 'External Service')])

    consale_amount = fields.Float(string="Total Amount")
    consale_currency = fields.Char(string='Currency')

    consale_payid = fields.Char(string='PayID')
    consale_eci = fields.Char(string='Electronic Commerce Indicator')
    consale_common_name = fields.Char(string='Common Name')
    consale_error_code = fields.Char(string='Error Code')
    consale_error_msg = fields.Char(string='Error Message')
    consale_ip_address = fields.Char(string='Caller IP Address')

    @api.model
    def _consale_form_get_tx_from_data(self, data):
        reference = data.get('reference')
        tx = self.search([('reference', '=', reference)])
        if not tx:
            raise ValidationError('No payment transaction found for reference %s' % reference)
        elif len(tx) > 1:
            raise ValidationError('Multiple payment transaction found for reference %s' % reference)
        return tx

    @api.model
    def _consale_form_get_invalid_parameters(self, tx, data):
        invalid_parameters = []

        # Compare the local amount with the amount from the PP
        if float_compare(float(data.get('amount', '0.0')), tx.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % tx.amount))

        # Compare the local currency with the currency of the pp
        if data.get('currency') != tx.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), tx.currency_id.name))

        return invalid_parameters

    @api.model
    def _consale_form_validate(self, tx, data):
        _logger.info("Validate payment transaction data for consale (tx ID %s)" % tx.id)

        # Check required fields
        required = ['acquirer_reference',
                    'consale_state',
                    'consale_transaction_date',
                    'consale_provider_name',
                    'consale_method',
                    'consale_method_brand',
                    'consale_amount',
                    'consale_currency']

        # Banktransfer Payment validations
        if data.get('consale_method', '') == 'banktransfer':
            consale_method_banktransfer_provider = data.get('consale_method_banktransfer_provider', '')
            if not consale_method_banktransfer_provider:
                raise ValidationError("The field 'consale_method_banktransfer_provider' is required for the payment "
                                      "method 'banktransfer'!")
            if consale_method_banktransfer_provider == 'frst':
                required += ['consale_method_account_owner',
                             'consale_method_account_iban',
                             'consale_method_account_bank']

        # Recurring Payment validations
        if data.get('consale_recurring_payment_ever_months', None):
            consale_recurring_payment_provider = data.get('consale_recurring_payment_provider', None)
            if not consale_recurring_payment_provider:
                raise ValidationError("The recurring payment provider 'consale_recurring_payment_provider' must be "
                                      "set for recurring payments!")
            if consale_recurring_payment_provider == 'frst':
                if not data.get('consale_method', '') == 'banktransfer':
                    raise ValidationError("Only 'banktransfer' method is allowed for recurring payment that should be "
                                          "executed by Fundraising Studio")

        # Check if any required field value is missing
        missing_fields = tuple(f for f in required if not data.get(f, False))
        if missing_fields:
            raise ValidationError("Fields missing: %s" % missing_fields)

        if data.get('consale_method', '') == 'other' and not data.get('consale_method_other', ''):
            raise ValidationError("Field 'consale_method_other' is empty!")

        # Use the consale state as the payment transaction state
        vals = data
        vals['state'] = data.get('consale_state')

        # Update the payment transaction and return the boolean results
        res = tx.write(vals)

        return True if res and tx.state in ('done', 'pending') else False
