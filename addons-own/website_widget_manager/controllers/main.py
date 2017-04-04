# -*- coding: utf-8 -*-
from openerp.http import request
from openerp.osv import orm

# Check for widget redirect urls to redirect if not opened in an iframe by java script (see website_domain_manager!)
# HINT: to inherit from _dispatch() was found at addons/crm/ir_http.py
class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        # ATTENTION: _dispatch() must called before anything else!
        dispatch = super(ir_http, self)._dispatch()

        # Return if there is not (jet) an env or this is not a httprequest or website request (e.g.: a backend request)
        if not hasattr(request, 'env') or not request.env \
                or not hasattr(request, 'httprequest') or not request.httprequest.host \
                or not hasattr(request, 'website') or not request.website:
            return dispatch

        # Search if there is an widget redirect url for the requeste path
        request_domain = request.httprequest.host.split(':', 1)[0]
        request_path = request.httprequest.path
        widget = request.env['website.widget_manager'].sudo().search(['&', '&',
                                                                      ('source_domain', '=like', 'request_domain'),
                                                                      ('source_page', '=like', 'request_path'),
                                                                      ('target_url', '!=', False)
                                                                      ])
        if widget:
            # TODO: Transfer all parameters from the request URI to target url iframe = source_url + source_page + request params
            request.session['noiframe_redirect_url'] = widget[0].target_url

        return dispatch
