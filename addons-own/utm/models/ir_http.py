# -*- coding: utf-8 -*-
from openerp.http import request
from openerp import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    #@classmethod
    def get_utm_domain_cookies(self):
        return request.httprequest.host

    #@classmethod
    def _set_utm(self, response):
        if isinstance(response, Exception):
            return response

        # In case there is no request yet (unbound object error catch)
        # https://github.com/OCA/e-commerce/issues/152
        # https://github.com/OCA/e-commerce/pull/190
        if not request:
            return response

        try:
            domain = self.get_utm_domain_cookies()
            for var, dummy, cook in request.env['utm.mixin'].tracking_fields():
                if var in request.params and request.httprequest.cookies.get(var) != request.params[var]:
                    response.set_cookie(cook, request.params[var], domain=domain)
        except Exception as e:
            pass

        return response


    #@classmethod
    def _dispatch(self):
        response = super(IrHttp, self)._dispatch()
        return self._set_utm(response)

    #@classmethod
    def _handle_exception(self, exc):
        response = super(IrHttp, self)._handle_exception(exc)
        return self._set_utm(response)
