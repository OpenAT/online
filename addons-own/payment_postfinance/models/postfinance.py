# -*- coding: utf-'8' "-*-"
__author__ = 'mkarrer'

import base64
try:
    import simplejson as json
except ImportError:
    import json
import logging
import pprint
from openerp.tools.misc import mod10r
from openerp.addons.payment.models.payment_acquirer import ValidationError
# Import the Postfinance Controller This is possible because we add payment_postfinance to the main class later on
from openerp.addons.payment_postfinance.controllers.main import PostfinanceController
from openerp.osv import osv, fields
from openerp.tools.float_utils import float_compare
from openerp.tools.float_utils import float_round
from openerp import SUPERUSER_ID
import re
_logger = logging.getLogger(__name__)


class EsrCustomerNumber(osv.Model):
    _inherit = 'res.partner.bank'

    _columns = {
        'esr_customer_number': fields.char(string='Postfinance ESR Customer Number')
    }


# This class modifies the payment.acquirer class: this will add new payment providers to odoo. Payment Providers Objects
# hold all the relevant data to talk with an payment provider like urls, secrets and data (tx_values)
#
# Since we do not talk to any external payment provider we do not need most of the methods and variables seen in the
# paypal or adyen pp.
class AcquirerPostfinance(osv.Model):
    _inherit = 'payment.acquirer'

    # Add a new Acquirer
    def _get_providers(self, cr, uid, context=None):
        providers = super(AcquirerPostfinance, self)._get_providers(cr, uid, context=context)
        providers.append(['postfinance', 'Postfinance'])
        return providers

    # Add Additional tx values for the aquirer button form
    # There is a hook inside the .render method in "addons/payment/models/payment_acquirer.py"
    # The .render method is called by "addons/website_sale/controllers/main.py" at route /shop/payment to render
    # the aquirer buttons. at this point partner_id and sales_order is normally known
    #
    # Hint: This .render method uses the original .render method of ir.ui.view in the end to render a qweb template
    #
    # The aquirer button rendering itself is triggered at addons/website_sale/controllers/main.py
    # line 659: "acquirer.button = payment_obj.render" at route /shop/payment
    #
    # Transaction values ar given to ".render". Inside render the above mentioned hook adds acquirer specific values to
    # partner_values and tx_values (which are pre-processed at "form_preprocess_values directly in render") and then
    # used in the dictionary qweb_context wich is used to render the qweb template for the acquirer button form
    def postfinance_form_generate_values(self, cr, uid, id, partner_values, tx_values, context=None):
        # postfinance_partner_values = dict(partner_values)
        # postfinance_partner_values.update({
        #         'esr_reference_number': '',
        #         'esr_customer_number': '',
        #         'esr_code_line': '',
        #     })

        # HINT: Address Format
        # Schuldneradressen sind immer in einem Block, also ohne Leerzeilen zu drucken.
        # Es duerfen keine Zusatzangaben angebracht ­werden
        # Schriftart: OCR-B1-Schrift

        # Get Sale Order
        salesorder_obj = self.pool.get('sale.order')
        salesorder_id = salesorder_obj.search(cr, SUPERUSER_ID,
                                              [('name', '=', tx_values.get('reference')), ], context=context)
        assert len(salesorder_id) == 1, \
            'ERROR: None or more than one Sales Order with name %s found!' % tx_values.get('reference')
        salesorder = salesorder_obj.browse(cr, SUPERUSER_ID, salesorder_id, context=context)

        # Get Currency from Sales Order
        currency_iso_code = salesorder.currency_id.name
        assert currency_iso_code in ['EUR', 'CHF'], 'ERROR: ESR Currency not EUR or CHF: %s' % currency_iso_code

        # Get Postfinance ESR Customer Number for the Sales Order Currency
        if not salesorder.company_id.currency_id:
            raise Exception('ERROR: No Default Currency found for Company %s' % salesorder.company_id.name)

        esr_customer_number = str()
        for bank_account in salesorder.company_id.bank_ids:
            # Use currency from bank account or if none found it has to be the default one from the company
            # (This is needed for the standard case: addon multy_currency not installed)
            currency_id = salesorder.company_id.currency_id
            if bank_account.currency_id:
                currency_id = bank_account.currency_id
            # Get the esr_customer_number
            if salesorder.currency_id == currency_id and bank_account.esr_customer_number:
                assert esr_customer_number == '', \
                    'ERROR: More than one ESR-Customer-Number found for %s Bank Accounts!' % currency_iso_code
                esr_customer_number = bank_account.esr_customer_number
        assert esr_customer_number, \
            'ERROR: Postfinance ESR Customer Number not found in %s Bank Accounts!' % currency_iso_code

        # Check Postfinance ESR Customer-Number
        # -------------------------------------
        # VV-XXX-P
        # VV = ESR Code ACHTUNG: ist NICHT das Selbe wie Transaktionsartcodes!
        # 01 = CHF
        # 03 = EUR
        # XXX = Ordnungsnummer (Kundennummer der Firma bei Postfinanze) (OHNE! vorlaufende Nullen)
        # P = Prüfziffer
        pattern = '([0-9]+)-([0-9]+)-([0-9]?)'
        try:
            esr_code = re.search(pattern, esr_customer_number).group(1)
            esr_customer = re.search(pattern, esr_customer_number).group(2)
            esr_customer_number_check = re.search(pattern, esr_customer_number).group(3)
        except:
            raise Exception('ERROR: Postfinance-ESR-Customer-Number %s has a wrong format!' % esr_customer_number)

        esr_customer_number_standard = mod10r(esr_code + '{0:06d}'.format(int(esr_customer)))

        assert esr_customer_number_standard[-1] == esr_customer_number_check, \
            'ERROR: Postfinance-ESR-Customer-Number %s has a wrong check number! Should be %s' % \
            (esr_customer_number, esr_customer_number_standard[-1])
        if currency_iso_code == 'EUR':
            assert esr_code == '03', 'ERROR: esr_code %s but currency EUR. Must be 03!' % esr_code
        if currency_iso_code == 'CHF':
            assert esr_code == '01', 'ERROR: esr_code %s but currency CHF. Must be 01!' % esr_code

        # Generate Kodierzeile Anfang
        # ---------------------------
        # VVXXXXXXXXXXP
        #   VV = Transaktionsartcodes für Record Typ 4 (ESR in CHF und EUR)
        #   01 = ESR Normal in CHF
        #   21 = ESR Normal in EUR
        #   XXXXXXXXXX = Betrag mit 2 Kommastellen !!!inkl. vorlaufende Nullen!!!
        #   P = Prüfziffer (MOD10r)
        #
        # HINT: Currency in EUR or CHF already asserted above!
        transaction_type = '01' if currency_iso_code == 'CHF' else '21'
        # HINT: CHF muessen auf 00 oder 05 Rappen gerundet werden (Schweizer Norm)
        # TODO: Check if Rounding to 05 is working for CH
        amountstring_2digits = str('{0:.2f}'.format(float_round(tx_values.get('amount'), 2))).replace('.', '')
        esr_code_line_start = mod10r(transaction_type + '{0:010d}'.format(int(amountstring_2digits)))
        assert len(esr_code_line_start) == 13, 'ERROR: ESR Code Line start is not 13 Char long but %s!' % \
                                               len(esr_code_line_start)

        # Generate esr_reference_number:
        # ------------------
        # AAAAAXXXXXXXXXXXXXXXXXXXXXP (26 Stellen + P = 27 Stellen)
        #   AAAAA = Instance Base Port
        #   XXXXXXXXXXXXXXXXXXXXX = Sales Order Number
        port = salesorder.company_id.instance_base_port
        assert len(port) == 5, "ERROR: Field instance_base_port for company not set or not 5 char long: %s" % port
        so_number = ''.join(re.findall(r'\d+', salesorder.name))
        so_number = '{0:021d}'.format(int(so_number))
        esr_reference_number = mod10r(port + so_number)

        # Generate Kodierzeile Ende (=Postfinance ESR Number)
        # -------------------------
        # VVXXXXXXP
        #   VV = ESR Typ (Code)
        #   XXXXXX = Ordnungsnummer !!!inkl. vorlaufende Nullen!!! (Kundennummer der Firma bei Postfinanze)
        #   P = Prüfziffer (MOD10r)
        esr_code_line = esr_code_line_start + '>' + esr_reference_number + '+ ' + esr_customer_number_standard + '>'
        print esr_code_line

        # Update Dict
        tx_values.update({
                'esr_reference_number': esr_reference_number,
                'esr_customer_number': esr_customer_number,
                'esr_code_line': esr_code_line,
            })

        return partner_values, tx_values



    # Define the Form URL (url that will be called when button with form is clicked)
    def postfinance_get_form_action_url(self, cr, uid, id, context=None):
        return '/payment/postfinance/feedback'




# This class creates the payment transaction objects. So the objects that are created through an checkout (payment)
# process
class PaymentTransactionPostfinance(osv.Model):
    _inherit = 'payment.transaction'

    _columns = {
        'esr_reference_number': fields.char('ESR Reference Number'),
        'esr_customer_number': fields.char('ESR Customer Number'),
        'esr_code_line': fields.char('ESR Full Code Line'),
    }

    # Get all related stored Transactions for the current Reference Number
    def _postfinance_form_get_tx_from_data(self, cr, uid, data, context=None):

        # the current sales order is stored in reference
        reference = data.get('reference')

        # search for transactions linked to this sales order
        tx_ids = self.search(cr, uid, [('reference', '=', reference),], context=context)
        if not tx_ids or len(tx_ids) > 1:
            error_msg = 'ESR Payment Transaction: received data for reference %s' % (pprint.pformat(reference))
            if not tx_ids:
                error_msg += '; no Transaction found'
            else:
                error_msg += '; multiple Transactions found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # return the payment.transaction object
        return self.browse(cr, uid, tx_ids[0], context=context)

    # Check the Received (tx) values against local (data) ones: Amount and the Currency
    # (This is not really needed since we are our own payment provider but for demonstration it is used here)
    def _postfinance_form_get_invalid_parameters(self, cr, uid, tx, data, context=None):
        invalid_parameters = []

        # Compare the local amount with the amount from the PP
        if float_compare(float(data.get('amount', '0.0')), tx.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % tx.amount))

        # Compare the local currency with the currency of the pp
        if data.get('currency') != tx.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), tx.currency_id.name))

        # Check esr_reference_number
        if not data.get('esr_reference_number'):
            invalid_parameters.append(('esr_reference_number',
                                       data.get('esr_reference_number'),
                                       'ESR Reference Number missing!'))

        # Check esr_customer_number
        if not data.get('esr_customer_number'):
            invalid_parameters.append(('esr_customer_number',
                                       data.get('esr_customer_number'),
                                       'ESR Customer Number missing!'))

       # Check esr_code_line
        if not data.get('esr_code_line'):
            invalid_parameters.append(('esr_code_line',
                                       data.get('esr_code_line'),
                                       'ESR Code Line missing!'))

        info_msg = 'Postfinance ESR Payment Transaction: Invalid Parameters %s' % (pprint.pformat(invalid_parameters))
        _logger.info(info_msg)
        print '----'
        print info_msg
        print '----'

        return invalid_parameters

    # Do the form validation and directly set the state of the payment.transaction to pending
    def _postfinance_form_validate(self, cr, uid, tx, data, context=None):
        _logger.info('Validated Postfinance ESR payment %s set to state pending.' % tx.reference)

        # Update State, Iban And BIC
        return tx.write({'state': 'pending',
                         'esr_reference_number': data.get('esr_reference_number'),
                         'esr_customer_number': data.get('esr_customer_number'),
                         'esr_code_line': data.get('esr_code_line'),
                         })
