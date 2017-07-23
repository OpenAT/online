# -*- coding: utf-'8' "-*-"
__author__ = 'mkarrer'

import base64
try:
    import simplejson as json
except ImportError:
    import json
import logging
import urlparse
import werkzeug.urls
import urllib2
import pprint

from openerp.addons.payment.models.payment_acquirer import ValidationError

# Import the payment_fsotransfer Controller
# HINT: this is only possilbebecause we add payment_fsotransfer to the main class later in this file
from openerp.addons.payment_fsotransfer.controllers.main import FsotransferController
from openerp.osv import osv, fields
from openerp.tools.float_utils import float_compare
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


# This class modifies the payment.acquirer class: this will add new payment providers to odoo. Payment Providers Objects
# hold all the relevant data to talk with an payment provider like urls, secrets and data (tx_values)
#
# Since we do not talk to any external payment provider we do not need most of the methods and variables seen in the
# paypal or adyen pp.
class AcquirerFsotransfer(osv.Model):
    _inherit = 'payment.acquirer'

    # Add a new Acquirer
    def _get_providers(self, cr, uid, context=None):
        providers = super(AcquirerFsotransfer, self)._get_providers(cr, uid, context=context)
        providers.append(['fsotransfer', 'FSOTransfer'])
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
    def fsotransfer_form_generate_values(self, cr, uid, id, partner_values, tx_values, context=None):
        _logger.info("fsotransfer_form_generate_values(): tx_values %s" % tx_values)
        # TODO: get initial value of do_not_send_payment_forms by payment acquirer
        tx_values.update({'do_not_send_payment_forms': None})
        _logger.warning("fsotransfer_form_generate_values(): tx_values: %s" % tx_values)
        return partner_values, tx_values

    # Define the Form URL (url that will be called when button with form is clicked)
    def fsotransfer_get_form_action_url(self, cr, uid, id, context=None):
        return '/payment/fsotransfer/feedback'


# This class creates the payment transaction objects. So the objects that are created through an checkout (payment)
# process
class PaymentTransactionFsotransfer(osv.Model):
    _inherit = 'payment.transaction'

    _columns = {
        'do_not_send_payment_forms': fields.boolean('Do not send payment forms'),
    }

    # Get all related stored Transactions for the current Reference Number
    def _fsotransfer_form_get_tx_from_data(self, cr, uid, data, context=None):

        # the current sales order is stored in reference
        reference = data.get('reference')

        # search for transactions linked to this sales order
        tx_ids = self.search(cr, uid, [('reference', '=', reference), ], context=context)
        if not tx_ids or len(tx_ids) > 1:
            error_msg = 'fsotransfer Payment Transaction: received data for reference %s' % (pprint.pformat(reference))
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
    def _fsotransfer_form_get_invalid_parameters(self, cr, uid, tx, data, context=None):
        invalid_parameters = []

        # Compare the local amount with the amount from the PP
        if float_compare(float(data.get('amount', '0.0')), tx.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % tx.amount))

        # Compare the local currency with the currency of the pp
        if data.get('currency') != tx.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), tx.currency_id.name))

        if invalid_parameters:
            info_msg = 'fsotransfer Payment Transaction: Invalid Parameters %s' % (pprint.pformat(invalid_parameters))
            _logger.info(info_msg)

        return invalid_parameters

    # do the form validation and directly set the state of the payment.transaction to pending
    def _fsotransfer_form_validate(self, cr, uid, tx, data, context=None):
        _logger.info('_fsotransfer_form_validate(): Validated fsotransfer payment for tx %s: set as pending: %s' %
                     (tx.reference, data))

        # Update State
        return tx.write({'state': 'pending',
                         'do_not_send_payment_forms': True if data.get('do_not_send_payment_forms') == 'on' else False})
