# -*- coding: utf-8 -*-
import werkzeug
from openerp.osv import orm
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)


class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        if not request or not request.httprequest:
            return super(ir_http, self)._dispatch()

        if request.httprequest.method == 'POST' \
                and request.params \
                and len(request.params) <= 2 \
                and 'signed_request' in request.params:
            _logger.warning("FACEBOOK REQUEST DETECTED! Redirect as GET request to: %s" % request.httprequest.url)
            return werkzeug.utils.redirect(request.httprequest.url, '303')

        return super(ir_http, self)._dispatch()
