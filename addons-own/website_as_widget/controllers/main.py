# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.osv import orm
from urlparse import urlparse

from openerp.addons.web.controllers.main import Session


# Extend the logout method to not throw an exception if other kwargs than redirect are given! e.g.: aswidget=True
class SessionAuthPartner(Session):

    # addons/web/controllers/main.py around line 865
    # '/web/session/logout', type='http', auth="none"
    @http.route()
    def logout(self, redirect='/web', **kwargs):

        # CHECK FOR ASWIDGET (before logout)
        # Check for aswidget in the current session
        aswidget = request.session.get('aswidget', False)
        # Check for an aswidget parameter in the kwargs
        # HINT: kwargs have a higher priority than the aswidget parameter stored in the session if any
        if kwargs.get('aswidget'):
            if kwargs.get('aswidget') not in ('False', 'false'):
                aswidget = True
            else:
                aswidget = False

        # LOGOUT and create a new request, session and cookie
        response = super(SessionAuthPartner, self).logout(redirect=redirect)

        # RESTORE ASWIDGET for the new session
        request.session['aswidget'] = aswidget

        # Return the final response with the new session
        return response


# DEPRICATED! only there for downward compatibility
class website_as_widget(http.Controller):
    @http.route(['/aswidget'], type='http', auth="public", website=True)
    def page_as_widget(self, *args, **kwargs):
        # get aswiddget from kwargs or set it to True if not found: So one could call the URL with &aswidget=False to
        # reset the session and show header and footer again
        request.session['aswidget'] = kwargs.get('aswidget', True)
        widgeturl = kwargs.get('widgeturl', '/')
        # local_redirect found at addons/web/controllers/main.py line 467
        return http.local_redirect(widgeturl, query=request.params, keep_hash=True)


# found at addons/crm/ir_http.py
# Test the URL of every request (better would be to only test the urls of the correct sub controller of
# addons/web/controllers/main.py class Home but it works and has no performance impact ;) )
class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        # Process the request first
        response = super(ir_http, self)._dispatch()

        # Check for aswidget before returning the response
        if hasattr(request, 'website') and request.website:

            # Check for aswidget in the URI authority (http://aswidget.datadialog.net)
            if 'aswidget' in request.httprequest.host:
                request.session['aswidget'] = True
            # Check for aswidget in the URI query (http://www.datadialog.net/?aswidget=True)
            elif 'aswidget' in request.httprequest.args:
                request.session['aswidget'] = False if request.httprequest.args.get('aswidget') in ['False', 'false'] \
                    else True

            # Check aswidget_domains
            if hasattr(request, 'env') and request.env:
                aswidget_domains = request.env['website.aswidget_domains']
                aswidget_domains = aswidget_domains.search([])
                base_url = str(urlparse(request.httprequest.base_url).hostname)
                for domain in aswidget_domains:
                    if domain.aswidget_domain and domain.aswidget_domain in base_url:
                        request.session['aswidget'] = True
                        if domain.redirect_url:
                            request.session['aswidget_redirect_url'] = domain.redirect_url

        return response
