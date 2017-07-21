# -*- coding: utf-'8' "-*-"
import logging
from copy import deepcopy
from openerp import SUPERUSER_ID
from openerp.http import request
from openerp.addons.website_sale.models.payment import PaymentTransaction

__author__ = 'mkarrer'
_logger = logging.getLogger(__name__)


# Replaces completely website_sale.models.payment >>> form_feedback()
def form_feedback(self, cr, uid, data, acquirer_name, context=None):
    tx = None
    tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name

    # Try to find related tx before form_feedback() is done
    # -----------------------------------------------------
    tx_state_start = False
    try:
        if hasattr(self, tx_find_method_name):
            tx = getattr(self, tx_find_method_name)(cr, uid, data, context=context)
            if tx:
                tx_state_start = deepcopy(tx.state)
    except Exception:
        _logger.info("Could not find a payment transaction before form_feedback()")

    # Call original odoo/addons/payment/models/payment_acquirer.py >>> form_feedback()
    # --------------------------------------------------------------------------------
    # HINT: This is what form_feedback does if implemented in the PP
    #   1.) '_%s_form_get_tx_from_data'
    #   2.) '_%s_form_get_invalid_parameters'
    #   3.) '_%s_form_validate'
    # HINT: RES could be True, False or, just if implemented by the PP, a method (which may return the TX id)
    res = super(PaymentTransaction, self).form_feedback(cr, uid, data, acquirer_name, context=context)

    # Try to find related tx after form_feedback() is done
    # ----------------------------------------------------
    try:
        if hasattr(self, tx_find_method_name):
            tx = getattr(self, tx_find_method_name)(cr, uid, data, context=context)

        # Log Information about the tx
        _logger.info('<%s> (ID %s) payment transaction processed: tx ref:%s, tx amount: %s',
                     acquirer_name,
                     tx.id if tx else 'n/a',
                     tx.reference if tx else 'n/a',
                     tx.amount if tx else 'n/a')

    except Exception:
        try:
            _logger.error("<%s> Could not find a payment transaction for data: \n%s\n" % (acquirer_name, data))
        except Exception:
            _logger.error("<%s> Could not find a payment transaction for given data!" % acquirer_name)
        finally:
            return False

    # Update sale order based on tx state
    # -----------------------------------
    try:
        if tx and tx.sale_order_id:
            # Payment done (or awaiting payment)
            if tx.state in ['pending', 'done'] and tx.sale_order_id.state in ['draft', 'sent']:
                _logger.info('<%s> (ID %s) payment transaction completed. Confirming sale order %s (ID %s)',
                             acquirer_name, tx.id, tx.sale_order_id.name, tx.sale_order_id.id)
                self.pool['sale.order'].action_button_confirm(cr, SUPERUSER_ID, [tx.sale_order_id.id], context=context)

            # Payment error
            if tx.state in ['cancel', 'error'] and tx.sale_order_id.state != 'cancel':
                _logger.error('<%s> (ID %s) payment transaction error! Cancel sale order %s (ID %s)', acquirer_name,
                              tx.id, tx.sale_order_id.name, tx.sale_order_id.id)
                self.pool['sale.order'].action_cancel(cr, SUPERUSER_ID, [tx.sale_order_id.id], context=context)

            # All other payment states
            if tx.state not in ['pending', 'done', 'cancel', 'error']:
                _logger.warning('<%s> (ID %s) unknown payment transaction state %s! Sale order %s (ID %s) in state %s',
                                acquirer_name, tx.id, tx.state, tx.sale_order_id.name, tx.sale_order_id.id,
                                tx.sale_order_id.state)
    except Exception as e:
        try:
            _logger.error("<%s> Could not change state of sale order %s (ID %s): \n%s\n" %
                          (acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id, repr(e)))
        except Exception:
            _logger.error("Could not change state of sale order!" % acquirer_name)
        finally:
            return False

    # Send an email if tx state has changed
    # -------------------------------------
    try:
        if tx.state != tx_state_start and not tx.acquirer_id.do_not_send_status_email:
            _logger.info("Payment status changed from %s to %s for payment transaction <%s> (ID %s)! "
                         "Sending information email 'fso_base.email_template_webshop' to partner for sale order %s !" %
                         (tx_state_start, tx.state, acquirer_name, tx.id, tx.sale_order_id.name))
            email_act = request.registry['sale.order'].action_quotation_send(cr, SUPERUSER_ID,
                                                                             [tx.sale_order_id.id],
                                                                             context=context,
                                                                             email_template_addon='fso_base',
                                                                             email_template_name='email_template_webshop')
            if email_act and email_act.get('context'):
                composer_obj = request.registry['mail.compose.message']
                composer_values = {}
                email_ctx = email_act['context']
                template_values = [
                    email_ctx.get('default_template_id'),
                    email_ctx.get('default_composition_mode'),
                    email_ctx.get('default_model'),
                    email_ctx.get('default_res_id'),
                ]
                composer_values.update(composer_obj.onchange_template_id(cr, SUPERUSER_ID, None, *template_values,
                                                                         context=context).get('value', {}))
                if not composer_values.get('email_from') and uid == request.website.user_id.id:
                    composer_values['email_from'] = request.website.user_id.company_id.email
                for key in ['attachment_ids', 'partner_ids']:
                    if composer_values.get(key):
                        composer_values[key] = [(6, 0, composer_values[key])]
                composer_id = composer_obj.create(cr, SUPERUSER_ID, composer_values, context=email_ctx)
                composer_obj.send_mail(cr, SUPERUSER_ID, [composer_id], context=email_ctx)
    except Exception as e:
        try:
            _logger.error("<%s> (ID %s) Could not send payment transaction status change e-mail! \n%s\n" %
                          (acquirer_name, tx.id, repr(e)))
        except Exception:
            _logger.error("Could not send payment transaction status change e-mail!")
        finally:
            pass

    return res


# ====================================================
# REPLACE THE ORIGINAL METHOD INSTEAD OF INHERITING IT
# ====================================================
# HINT: This is sometimes called monkey patching ;)
# ATTENTION: We need to do this because in the form_feedback() of website_sale an quotation e-mail is send if the sale
#            order state is draft and the tx is anything but "done" or "cancel" which is definitely NOT what we want!
#            As a bonus we can add all logic former placed and duplicated a lot in the dadi payment methods inside our
#            [pmname]_form_feedback() like the custom email after tx state change.
# HINT: If any other addon also inherits from website_sale > form_feedback() and calls super this method will be called
#       and not the one in website_sale which is exactly what we want and expect!
PaymentTransaction.form_feedback = form_feedback
