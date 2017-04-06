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

        # REDIRECT
        # For source_screenshot only ('noiframeredirect' should never be in url query except for the widget-screenshots)
        if 'noiframeredirect' in request.params:
            request.session.pop('noiframe_redirect_url', False)
            return dispatch

        request_domain = request.httprequest.host.split(':', 1)[0]
        request_path = request.httprequest.path.split('?', 1)[0]
        widget = request.env['website.widget_manager'].sudo().search(['&', '&',
                                                                      ('source_domain', '=', request_domain),
                                                                      ('source_page', '=', request_path),
                                                                      ('target_url', '!=', False)
                                                                      ])
        if widget:
            # TODO: Maybe we should transfer all parameters from the request URI to
            #       the target url iframe parameter too ?!?
            request.session['noiframe_redirect_url'] = widget[0].target_url

        return dispatch
