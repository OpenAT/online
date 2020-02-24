# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class FRSTController(http.Controller):
    _accept_url = '/payment/frst/feedback'

    # This route is called through the "pay now" button on the /shop/payment page
    @http.route(['/payment/frst/feedback'], type='http', auth='none', website=True)
    def frst_form_feedback(self, **post):
        cr = request.cr
        uid = SUPERUSER_ID
        context = request.context

        _logger.info('Beginn Form Feedback for FRST PaymentProvider with post data %s', pprint.pformat(post))
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'frst', context)

        # Finally redirect to /shop/payment/validate
        # HINT: /shop/payment/validate is the default url hard coded in a lot of places
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
