# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class PostfinanceController(http.Controller):
    _accept_url = '/payment/postfinance/feedback'

    # This route is called through the "pay now" button on the /shop/payment page
    @http.route(['/payment/postfinance/feedback'], type='http', auth='none', website=True)
    def postfinance_form_feedback(self, **post):
        cr = request.cr
        uid = SUPERUSER_ID
        context = request.context

        _logger.info('Beginn Form Feedback for Postfinance PaymentProvider with post data %s', pprint.pformat(post))
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'postfinance', context=context)

        return werkzeug.utils.redirect(post.pop('return_url', '/'))
