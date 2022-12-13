# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import openerp
from openerp.http import Response


_logger = logging.getLogger(__name__)


def wsgi_postload():
    if openerp.service.wsgi_server:
        _logger.warning("WSGI server found.")
        root_handler = openerp.service.wsgi_server.module_handlers[0]

        if root_handler and type(root_handler) is openerp.http.Root:
            _logger.warning("WSGI root handler found, monkey patching get_response() to include \"SameSite=None; Secure\" cookie attributes")
            root_handler.get_response = get_response.__get__(root_handler, openerp.http.Root)
        else:
            _logger.warning("WSGI root handler was null or of unexpected type, doing nothing.")

    else:
        _logger.warning("WSGI server was NOT found doing nothing.")


# This is basically a copy of the get_response method of the Root class
# in /odoo/openerp/http.py, with code added to add cookie attributes
# (see for loop at the end)
def get_response(self, httprequest, result, explicit_session):
    if isinstance(result, Response) and result.is_qweb:
        try:
            result.flatten()
        except(Exception), e:
            if request.db:
                result = request.registry['ir.http']._handle_exception(e)
            else:
                raise

    if isinstance(result, basestring):
        response = Response(result, mimetype='text/html')
    else:
        response = result

    if httprequest.session.should_save:
        if httprequest.session.rotate:
            self.session_store.delete(httprequest.session)
            httprequest.session.sid = self.session_store.generate_key()
            httprequest.session.modified = True
        self.session_store.save(httprequest.session)
    # We must not set the cookie if the session id was specified using a http header or a GET parameter.
    # There are two reasons to this:
    # - When using one of those two means we consider that we are overriding the cookie, which means creating a new
    #   session on top of an already existing session and we don't want to create a mess with the 'normal' session
    #   (the one using the cookie). That is a special feature of the Session Javascript class.
    # - It could allow session fixation attacks.
    if not explicit_session and hasattr(response, 'set_cookie'):
        response.set_cookie('session_id', httprequest.session.sid, max_age=90 * 24 * 60 * 60)

    # Search for the session cookie header, and add Samesite attributes
    for idx in range(0, len(response.headers)):
        if response.headers[idx][0] == 'Set-Cookie' and response.headers[idx][1].startswith(b'session_id'):
            new_cookie_value = response.headers[idx][1] + b'; SameSite=None; Secure;'
            response.headers[idx] = ('Set-Cookie', new_cookie_value)

    return response
