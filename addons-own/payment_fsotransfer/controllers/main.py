# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class FsotransferController(http.Controller):
    _accept_url = '/payment/fsotransfer/feedback'

    # This route is called through the "pay now" button on the /shop/payment page
    @http.route(['/payment/fsotransfer/feedback'], type='http', auth='none', website=True)
    def fsotransfer_form_feedback(self, **post):
        cr = request.cr
        uid = SUPERUSER_ID
        context = request.context

        _logger.info('Begin Form Feedback for fsotransfer PaymentProvider with post data %s', pprint.pformat(post))


        # Get the Tx related to the post data of ogone
        tx_obj = request.registry['payment.transaction']
        tx = getattr(tx_obj, '_fsotransfer_form_get_tx_from_data')(cr, SUPERUSER_ID, post, context=context)

        # Prepare Variables
        state_old = False
        do_not_send_status_email = False
        redirect_url_after_form_feedback = None

        # Get Redirect URL from website settings
        if request.website:
            redirect_url_after_form_feedback = request.website.redirect_url_after_form_feedback or None

        if tx:
            # Store Current State of the transaction
            state_old = tx.state
            if tx.acquirer_id:
                do_not_send_status_email = tx.acquirer_id.do_not_send_status_email

                # Overwrite redirect URL from payment-provider setting
                redirect_url_after_form_feedback = tx.acquirer_id.redirect_url_after_form_feedback

                # Overwrite redirect URL from sales-order root_cat setting
                if tx.sale_order_id \
                        and tx.sale_order_id.cat_root_id \
                        and tx.sale_order_id.cat_root_id.redirect_url_after_form_feedback:
                    redirect_url_after_form_feedback = tx.sale_order_id.cat_root_id.redirect_url_after_form_feedback
        # Error Transaction not found
        else:
            _logger.error('Could not find correct Transaction for fsotransfer PP!')
            if redirect_url_after_form_feedback:
                return request.redirect(redirect_url_after_form_feedback)
            else:
                return request.redirect(request.registry.get('last_shop_page') or request.registry.get('last_page') or '/')

        # Update the payment.transaction and the Sales Order:
        # The sales order state will be updated in website_sale_payment_fix "form_feedback" method
        # INFO: form_feedback is also inherited by website_sale and website_sale_payment_fix
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'fsotransfer', context=context)

        # If the state changed send an E-Mail (have to do it here since we do not call /payment/validate)
        # HINT: we call a special E-Mail template "email_template_webshop" defined in website_sale_payment_fix
        #       for this to work we extended "action_quotation_send" interface with email_template_modell and ..._name
        if tx.state != state_old and not do_not_send_status_email:
            _logger.info('fsotransfer PP: Send E-Mail for Sales order: \n%s\n', pprint.pformat(tx.sale_order_id.name))
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
                composer_values.update(composer_obj.onchange_template_id(cr, SUPERUSER_ID, None, *template_values, context=context).get('value', {}))
                if not composer_values.get('email_from') and uid == request.website.user_id.id:
                    composer_values['email_from'] = request.website.user_id.company_id.email
                for key in ['attachment_ids', 'partner_ids']:
                    if composer_values.get(key):
                        composer_values[key] = [(6, 0, composer_values[key])]
                composer_id = composer_obj.create(cr, SUPERUSER_ID, composer_values, context=email_ctx)
                composer_obj.send_mail(cr, SUPERUSER_ID, [composer_id], context=email_ctx)

        # TODO: all stuff from website_sale payment fix was removed!!! Therefore we MUST DO
        #       the stuff from /payment/validate here !!!

        # Redirect ot our own Confirmation page (instead of calling /payment/validate)
        # all the stuff that could be done by /payment/validate for SO was already done by website_sale_payment_fix
        # "form_feedback" so we are no longer session variable dependent!
        if tx:
            if redirect_url_after_form_feedback and '?' not in redirect_url_after_form_feedback:
                    redirect_url_after_form_feedback += '?'
            # Add the order_id to the GET variables of the redirect URL
            order_id = '&order_id='
            if tx.sale_order_id:
                order_id += str(tx.sale_order_id.id)
            if redirect_url_after_form_feedback:
                return request.redirect(redirect_url_after_form_feedback + order_id)
            else:
                return request.redirect('/shop/confirmation_static?' + order_id)
