# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.osv import orm
from openerp.addons.auth_partner.fstoken_tools import fstoken_check
from openerp.addons.web.controllers.main import login_and_redirect

from urllib import urlencode
from urlparse import urlparse, parse_qs, urlunparse


import logging
_logger = logging.getLogger(__name__)


# add fs_ptoken to the session if in URL or post args
class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        # Process the request first
        response = super(ir_http, self)._dispatch()

        # In case there is no request yet (unbound object error catch)
        # https://github.com/OCA/e-commerce/issues/152
        # https://github.com/OCA/e-commerce/pull/190
        if not request:
            return response

        # Check for fs_ptoken before returning the requests response
        if hasattr(request, 'website') and request.website:

            fs_ptoken = request.httprequest.args.get('fs_ptoken')
            if fs_ptoken:

                # Compute the new url but without the fs_ptoken appended for security reasons
                request_url = request.httprequest.url
                url_parsed = urlparse(request_url)
                query_dict = parse_qs(url_parsed.query, keep_blank_values=True)
                query_dict.pop('fs_ptoken', None)
                url_parsed_clean = url_parsed._replace(query=urlencode(query_dict, True))
                redirect_url = urlunparse(url_parsed_clean)

                # Check token and login if valid
                # HINT: If the token is wrong or the login fails there is no message or hint at all
                #       which is the intended behaviour
                _logger.info('Check fs_ptoken %s in _dispatch()' % fs_ptoken)
                token_record, user, errors = fstoken_check(fs_ptoken)

                # Log every successful token request
                if token_record:
                    _logger.info('FS-Token (%s) found for res.partner %s (%s)'
                                 % (token_record.id, token_record.partner_id.name, token_record.partner_id.id))

                    if hasattr(request, 'session') and hasattr(request.session, 'context') and request.session.context:
                        request.session.context['fs_ptoken'] = token_record.name
                else:
                    _logger.info('Invalid or expired fs_ptoken given: %s!' % fs_ptoken)
                    # DISABLED BY MIKE because too aggressive - would kick logged in user just because they reuse an
                    #                  an expired token link in one of their valid e-mails
                    # request.session.logout(keep_db=True)
                    if hasattr(request, 'session') and hasattr(request.session, 'context') and request.session.context:
                        request.session.context.pop('fs_ptoken', False)
                        request.session.context.pop('fs_origin', False)

                # Login and redirect if needed
                if token_record and user and user.id != request.uid:
                    _logger.info('Login by FS-Token (%s) for res.user with login %s (%s) and redirect to %s'
                                 % (token_record.id, user.login, user.id, request.httprequest.url))
                    # ATTENTION: !!! It is VERY important to logout before any login to destroy the old session !!!
                    _logger.info('Destroy session before token login! (request.session.logout(keep_db=True))')
                    request.session.logout(keep_db=True)
                    # abort_and_redirect(request.httprequest.url)
                    res = login_and_redirect(request.db, user.login, token_record.name,
                                             redirect_url=redirect_url)

                    # Update the 'new context after login' with fs_ptoken and fs_origin
                    if hasattr(request, 'session') and hasattr(request.session, 'context') and request.session.context:
                        request.session.context['fs_ptoken'] = token_record.name
                        request.session.context['fs_origin'] = token_record.fs_origin or False
                    return res

                # If the token was not valid we still redirect to the initially called url but without the fs_ptoken
                return request.redirect(redirect_url)

        return response
