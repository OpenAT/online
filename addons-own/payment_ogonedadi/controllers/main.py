# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class OgonedadiController(http.Controller):
    _accept_url = '/payment/ogonedadi/test/accept'
    _decline_url = '/payment/ogonedadi/test/decline'
    _exception_url = '/payment/ogonedadi/test/exception'
    _cancel_url = '/payment/ogonedadi/test/cancel'

    @http.route([
        '/payment/ogonedadi/accept', '/payment/ogonedadi/test/accept',
        '/payment/ogonedadi/decline', '/payment/ogonedadi/test/decline',
        '/payment/ogonedadi/exception', '/payment/ogonedadi/test/exception',
        '/payment/ogonedadi/cancel', '/payment/ogonedadi/test/cancel',
    ], type='http', auth='none', website=True)
    def ogonedadi_form_feedback(self, **post):
        """ Ogone uses GET requests, at least for accept """
        _logger.info('Ogonedadi: entering form_feedback with post data: \n%s\n', pprint.pformat(post))  # debug
        cr, uid, context = request.cr, SUPERUSER_ID, request.context

        # Update the payment.transaction and the Sales Order:
        # form_feedback will call finally _ogonedadi_form_validate (call besides others) and return True or False
        # INFO: form_feedback is also inherited by website_sale and website_sale_payment_fix
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'ogonedadi', context=context)

        # Finally redirect to /shop/payment/validate
        # HINT: /shop/payment/validate is the default url hard coded in a lot of places
        return_url = post.pop('return_url', '/')
        _logger.info('Ogonedadi: Exiting form_feedback to return_url "%s"! (HINT: Normally this would be '
                     '/shop/payment/validate to calculate the redirect_url_after_form_feedback and to clear the session'
                     'data for an empty cart!)' % return_url)
        return werkzeug.utils.redirect(return_url)

    # TODO: This is experimental but would be nice to use a odoo page as a template for ogone
    # Add a route for the ogone template
    @http.route(['/shop/ogonepayment', '/shop/ogonepayment.html'], type='http', auth="public", website=True)
    def ogonepayment(self, **post):
        cr, uid, context = request.cr, request.uid, request.context

        # get the current URL of the webpage to set the absolute links for the CSS Files in the template
        values = {
            "url": request.registry['ir.config_parameter'].get_param(cr, SUPERUSER_ID, 'web.base.url'),
            "dbname": cr.dbname
        }

        return request.website.render("payment_ogonedadi.ogonepayment", values)
