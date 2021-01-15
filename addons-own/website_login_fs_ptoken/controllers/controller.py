# -*- coding: utf-8 -*-
##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import http
from openerp.http import request
from openerp import fields
from openerp.tools.translate import _
from openerp.addons.auth_partner.fstoken_tools import fstoken_check
from openerp.addons.web.controllers.main import login_and_redirect

import locale
import urllib2
import datetime
import logging
_logger = logging.getLogger(__name__)


class AuthPartnerForm(http.Controller):

    @http.route(['/web/login/fs_ptoken'], auth='public', website=True)
    def web_login_fs_ptoken(self, **kwargs):
        fs_ptoken = kwargs.get('fs_ptoken', '')
        redirect_url_after_token_login = kwargs.get('redirect_url_after_token_login', '')

        # Form Template
        form_template = 'website_login_fs_ptoken.token_login_form'

        # Messages
        tlf_messages = list()
        tlf_warning_messages = list()
        tlf_error_messages = list()

        # Field Errors
        field_errors = dict()

        # Honey Pot Field Test
        if kwargs.get('tlf_hpf'):
            if request.uid != request.website.user_id.id:
                tlf_error_messages.append(_('Data found in field with label: "Do not enter data here please!"'))
            return http.request.render(form_template, {
                'kwargs': dict(),
                'fs_ptoken': '',
                'redirect_url_after_token_login': urllib2.quote(redirect_url_after_token_login),
            })

        # Check Token
        if fs_ptoken:
            # Check the token
            token_record, token_user, token_error = fstoken_check(fs_ptoken)

            # VALID TOKEN (= Valid res.partner and valid res.user)
            if token_record:

                # Redirect URL
                redirect_url = redirect_url_after_token_login
                if not redirect_url:
                    tlf_messages += _("Success!")
                    redirect_url = '/web/login/fs_ptoken?fs_ptoken=%s' % urllib2.quote(fs_ptoken)

                # Login and Redirect
                _logger.info('Login by /web/login/fs_ptoken with token %s, user.login %s (%s)! Redirect to %s'
                             % (token_record.id, token_user.login, token_user.id, redirect_url))
                return login_and_redirect(request.db, token_user.login, token_record.name,
                                          redirect_url=redirect_url)
            # INVALID TOKEN
            if token_error:
                field_errors['fs_ptoken'] = 'invalid_fs_ptoken'
                tlf_error_messages += token_error

        return http.request.render(form_template,
                                   {'kwargs': kwargs,
                                    'fs_ptoken': fs_ptoken,
                                    'redirect_url_after_token_login': urllib2.quote(redirect_url_after_token_login),
                                    # Messages
                                    'tlf_messages': tlf_messages,
                                    'tlf_warning_messages': tlf_warning_messages,
                                    'tlf_error_messages': tlf_error_messages,
                                    # Field Errors
                                    'field_errors': field_errors,
                                    })


