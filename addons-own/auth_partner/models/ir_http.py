# -*- coding: utf-8 -*-
import werkzeug

from urllib import urlencode
from urlparse import urlparse, parse_qs, urlunparse

from openerp.osv import orm
from openerp.http import request, local_redirect
from openerp.addons.auth_partner.fstoken_tools import fstoken_check, log_token_usage, store_token_usage
from openerp.addons.web.controllers.main import login_and_redirect, set_cookie_and_redirect


def clean_url_from_fs_ptoken(url):
    request_url = request.httprequest.url
    url_parsed = urlparse(request_url)
    query_dict = parse_qs(url_parsed.query, keep_blank_values=True)
    query_dict.pop('fs_ptoken', None)
    url_parsed_clean = url_parsed._replace(query=urlencode(query_dict, True))
    url_no_fs_ptoken = urlunparse(url_parsed_clean)
    return url_no_fs_ptoken


class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        if not request or not request.httprequest:
            return super(ir_http, self)._dispatch()

        # Get fs_ptoken from url arguments
        fs_ptoken = request.httprequest.args.get('fs_ptoken', None)
        if not fs_ptoken:
            return super(ir_http, self)._dispatch()

        # Clean the url from the fs_ptoken parameter
        url_no_fs_ptoken = clean_url_from_fs_ptoken(request.httprequest.url)
        # redirect_no_fs_ptoken = set_cookie_and_redirect(url_no_fs_ptoken)
        redirect_no_fs_ptoken = werkzeug.utils.redirect(url_no_fs_ptoken, '303')

        # Check the fs_ptoken
        token_record, token_user, token_errors = fstoken_check(fs_ptoken)
        if not token_record or token_errors:
            # Log the token access error
            log_token_usage(fs_ptoken, token_record, token_user, token_errors, request.httprequest)
            # Remove token and token-fs-origin from context
            if hasattr(request, 'session') and hasattr(request.session, 'context'):
                request.session.context.pop('fs_ptoken', False)
                request.session.context.pop('fs_origin', False)
            return redirect_no_fs_ptoken

        # Do nothing if the token_user is already logged in
        if token_user.id == request.session.uid:
            return redirect_no_fs_ptoken

        # Logout current user (to destroy the session and clean the cache)
        request.session.logout(keep_db=True)

        # Login token_user and redirect to url without fs_ptoken (to avoid copy and paste of the url with token)
        login = token_user.login
        password = token_record.name
        redirect = login_and_redirect(request.db, login, password, redirect_url=url_no_fs_ptoken)

        # Add token and token-fs-origin to the context (after login_and_redirect because it may change the env)
        if hasattr(request, 'session') and hasattr(request.session, 'context'):
            request.session.context['fs_ptoken'] = token_record.name
            request.session.context['fs_origin'] = token_record.fs_origin or False

        # Log successful token usage
        log_token_usage(fs_ptoken, token_record, token_user, token_errors, request.httprequest)

        # Store successful token usage
        store_token_usage(fs_ptoken, token_record, token_user, request.httprequest)

        return redirect
