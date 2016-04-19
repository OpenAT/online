# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.osv import orm
from urlparse import urlparse

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
        response = super(ir_http, self)._dispatch()

        if request.website:

            # Check for aswidget
            if 'aswidget' in request.httprequest.host:
                request.session['aswidget'] = True
            elif 'aswidget' in request.httprequest.args:
                request.session['aswidget'] = False if request.httprequest.args.get('aswidget') in ['False', 'false'] \
                    else True

            # Global redirect if not called from a configuration URL
            base_url = str(urlparse(request.httprequest.base_url).hostname)
            # localhost and datadialog.net are Added for safety reasons ;)
            config_urls = 'localhost;datadialog.net;'
            config_urls += request.website.global_configuration_urls or ''
            # If a global redirect url is set
            # and the base_url is not in the config_urls redirect to the global_redirection url
            if request.website.global_redirect_url \
                    and not request.session.get('aswidget') \
                    and base_url not in config_urls:
                # TODO: Check if there is a root_cat and if the root_cat has a global_redirect_url
                #       if so - redirect to this url ;)
                return request.redirect(request.website.global_redirect_url)
        return response
