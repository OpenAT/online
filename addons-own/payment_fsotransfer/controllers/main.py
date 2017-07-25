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
    @http.route(['/payment/fsotransfer/feedback'], type='http', auth='none')
    def fsotransfer_form_feedback(self, **post):
        cr = request.cr
        uid = SUPERUSER_ID
        context = request.context

        _logger.info('Begin Form Feedback for fsotransfer PaymentProvider with post data %s', pprint.pformat(post))
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'fsotransfer', context)

        # Finally redirect to /shop/payment/validate
        # HINT: /shop/payment/validate is the default url hard coded in a lot of places
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
