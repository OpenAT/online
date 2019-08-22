# -*- coding: utf-'8' "-*-"
import logging
from copy import deepcopy
from openerp import SUPERUSER_ID
from openerp.http import request
from openerp.addons.website_sale.models.payment import PaymentTransaction

__author__ = 'mkarrer'
_logger = logging.getLogger(__name__)


# Replaces completely website_sale.models.payment >>> form_feedback()
# HINT: This would make further inheritance still possible
# ATTENTION: The replacement is done at the end of this file!
#
# We do this to
#     - update the sale order state and
#     - to send an email if the state of the payment transaction changes
def form_feedback(self, cr, uid, data, acquirer_name, context=None):
    tx = None
    tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name

    # Get payment transaction state before form_feedback
    # --------------------------------------------------
    tx_state_start = False
    if hasattr(self, tx_find_method_name):
        try:
            tx = getattr(self, tx_find_method_name)(cr, uid, data, context=context)
        except TypeError:
            _logger.warning("Try to call %s in new api format" % tx_find_method_name)
            tx = getattr(self, tx_find_method_name)(data)
            pass
    if tx:
        tx_state_start = deepcopy(tx.state)
    else:
        _logger.info("Could not find a payment transaction before form_feedback()")

    # Call original odoo/addons/payment/models/payment_acquirer.py >>> form_feedback()
    # --------------------------------------------------------------------------------
    # HINT: This is what form_feedback does if implemented in the PP
    #   1.) '_%s_form_get_tx_from_data'
    #   2.) '_%s_form_get_invalid_parameters'
    #   3.) '_%s_form_validate'
    # HINT: RES could be True, False or, just if implemented by the PP, a method (which may return the TX id)
    try:
        res = super(PaymentTransaction, self).form_feedback(cr, uid, data, acquirer_name, context=context)
    except TypeError:
        _logger.warning("Try to call form_feedback() in new api format")
        res = super(PaymentTransaction, self).form_feedback(data, acquirer_name)

    # Get payment transaction state after form_feedback
    # -------------------------------------------------
    try:
        if hasattr(self, tx_find_method_name):
            try:
                tx = getattr(self, tx_find_method_name)(cr, uid, data, context=context)
            except TypeError:
                _logger.warning("Try to call %s in new api format" % tx_find_method_name)
                tx = getattr(self, tx_find_method_name)(data)

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

            # Payment done but sale order is already confirmed
            elif tx.state in ['pending', 'done'] and tx.sale_order_id.state in ['progress', 'manual', 'done']:
                _logger.info('<%s> (ID %s) payment transaction completed. Sale order already confirmed %s (ID %s)',
                             acquirer_name, tx.id, tx.sale_order_id.name, tx.sale_order_id.id)

            # Payment error
            elif tx.state in ['cancel', 'error'] and tx.sale_order_id.state != 'cancel':
                _logger.error('<%s> (ID %s) payment transaction error or canceled by user! '
                              'Cancel sale order %s (ID %s)',
                              acquirer_name, tx.id, tx.sale_order_id.name, tx.sale_order_id.id)
                self.pool['sale.order'].action_cancel(cr, SUPERUSER_ID, [tx.sale_order_id.id], context=context)

            # Payment and sale order still 'draft'
            elif tx.state == 'draft' and tx.sale_order_id.state == 'draft':
                _logger.info('Sale order and payment transaction are still in state draft. Nothing to do!')

            # All other unexpected payment and sale order state combinations
            # HINT: This substitutes the old payment_fix addon and makes sure the cart is empty if something unexpected
            #       happened
            else:
                _logger.error('<%s> (TXID %s) unknown payment transaction state %s and Sale order %s (ID %s) state %s. '
                              'combination! Trying to set the sale order state to "send" if it is "draft" to avoid '
                              'further modifications of the sale order and to empty the shopping cart.',
                              acquirer_name, tx.id, tx.state, tx.sale_order_id.name, tx.sale_order_id.id,
                              tx.sale_order_id.state)
                # HINT: Check the long comment below to understand where this is taken from :)
                self.pool['sale.order'].signal_workflow(cr, SUPERUSER_ID, [tx.sale_order_id.id], 'quotation_sent')

    except Exception as e:
        try:
            _logger.error("<%s> Could not change state of sale order %s (ID %s): \n%s\n" %
                          (acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id, repr(e)))
        except Exception:
            _logger.error("Could not change state of sale order!" % acquirer_name)
        finally:
            return False

    # Queue an email if tx state has changed
    # --------------------------------------
    try:
        if tx.state != tx_state_start and not tx.acquirer_id.do_not_send_status_email:
            _logger.info("Payment status changed from %s to %s for payment transaction <%s> (ID %s)! "
                         "Sending information email 'fso_base.email_template_webshop' to partner for sale order %s !" %
                         (tx_state_start, tx.state, acquirer_name, tx.id, tx.sale_order_id.name))

            # ATTENTION: This was deactivated since we already set the sale order to 'sent' above in case of an
            #            unexpected state combination which is way easier to understand!
            #            Basically all this code just resembled the behavior of the form_feedback() from website_sale
            #            where force_quotation_send(): creates a composer object and sends the email directly without
            #            queueing.
            #            email.template send_mail() has the advantage to queue the mail instead of an mail.mail
            #            composer wizard object where we need to send the mail immediately
            # HINT: Action quotation send would normally open an email wizard gui to created and edit the email for
            #       the customer. This E-Mail wizard is hard-coded to the e-mail template 'email_template_edi_sale'
            #       and will also add 'mark_so_as_sent': True to the context. 'mark_so_as_sent' will trigger
            #       signal_workflow(cr, uid, [context['default_res_id']], 'quotation_sent') in sale.py > send_mail()
            #       All of this seems overly complicated!
            #       In any case send_mail() would set our sale order from draft to send here because 'mark_so_as_sent'
            #       is added in the context by action_quotation_send(). Basically this means we would always change
            #       the status of the sale order at least from 'draft' to 'send' if the tx.state changes
            #       The workflow seems to make sure that the sale order will not be set from e.g. 'confirmed' back to
            #       'send' again!
            #       In Summary this means: If the payment transaction has any other state than its initial state of
            #       'draft' we will set the sale order state at least to 'send' to prevent further editing.
            # email_act = request.registry['sale.order'].action_quotation_send(cr, SUPERUSER_ID,
            #                                                                  [tx.sale_order_id.id],
            #                                                                  context=context,
            #                                                                  email_template_addon='fso_base',
            #                                                                  email_template_name='email_template_webshop')
            # if email_act and email_act.get('context'):
            #     composer_obj = request.registry['mail.compose.message']
            #     composer_values = {}
            #     email_ctx = email_act['context']
            #     template_values = [
            #         email_ctx.get('default_template_id'),
            #         email_ctx.get('default_composition_mode'),
            #         email_ctx.get('default_model'),
            #         email_ctx.get('default_res_id'),
            #     ]
            #     composer_values.update(composer_obj.onchange_template_id(cr, SUPERUSER_ID, None, *template_values,
            #                                                              context=context).get('value', {}))
            #     if not composer_values.get('email_from') and uid == request.website.user_id.id:
            #         composer_values['email_from'] = request.website.user_id.company_id.email
            #     for key in ['attachment_ids', 'partner_ids']:
            #         if composer_values.get(key):
            #             composer_values[key] = [(6, 0, composer_values[key])]
            #     composer_id = composer_obj.create(cr, SUPERUSER_ID, composer_values, context=email_ctx)
            #     composer_obj.send_mail(cr, SUPERUSER_ID, [composer_id],  context=email_ctx)

            # Send queued mail by email.template send_mail()
            template_id = self.pool['ir.model.data'].get_object_reference(cr, SUPERUSER_ID,
                                                                          'fso_base',
                                                                          'email_template_webshop')[1]
            mail_id = self.pool['email.template'].send_mail(cr, SUPERUSER_ID, template_id, tx.sale_order_id.id,
                                                            force_send=False, context=context)
            assert mail_id, 'Email was not created!'
            _logger.info('Payment Transaction Status E-Mail was created with id %s', mail_id)

    except Exception as e:
        try:
            _logger.error("<%s> (ID %s) Could not prepare and queue payment transaction status e-mail! \n%s\n" %
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
