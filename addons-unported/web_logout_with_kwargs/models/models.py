# -*- coding: utf-8 -*-
import urlparse
from urllib import urlencode
from openerp import http
from openerp.addons.web.controllers.main import Session


# Extend the logout method to not throw an exception if other kwargs than redirect are given!
class SessionAuthPartner(Session):

    # addons/web/controllers/main.py around line 865
    # @http.route('/web/session/logout', type='http', auth="none")
    @http.route()
    def logout(self, redirect='/web', **kwargs):

        # Create the redirect URL including the kwargs
        url = redirect
        url_parts = list(urlparse.urlparse(url))
        params = dict(urlparse.parse_qsl(url_parts[4]))
        params.update(kwargs)
        url_parts[4] = urlencode(params)
        redirect = urlparse.urlunparse(url_parts)

        # LOGOUT and create a new request, session and cookie
        return super(SessionAuthPartner, self).logout(redirect=redirect)
