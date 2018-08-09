# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.osv import orm
from openerp.addons.auth_partner.fstoken_tools import fstoken_check
from openerp.addons.web.controllers.main import login_and_redirect

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

                # Check token and login if valid
                # HINT: If the token is wrong or the login fails there is no message or hint at all
                #       which is the intended behaviour
                token_record, user, errors = fstoken_check(fs_ptoken)

                # Log every successful token request
                if token_record:
                    _logger.info('Valid FS-Token (%s) found for res.partner %s (%s)'
                                 % (token_record.id, token_record.partner_id.name, token_record.partner_id.id))

                    if hasattr(request, 'session') and hasattr(request.session, 'context') and request.session.context:
                        request.session.context['fs_ptoken'] = token_record.name
                else:
                    if hasattr(request, 'session') and hasattr(request.session, 'context') and request.session.context:
                        request.session.context.pop('fs_ptoken', False)

                # Login and redirect if needed
                if token_record and user and user.id != request.uid:
                    _logger.info('Login by FS-Token (%s) for res.user with login %s (%s) and redirect to %s'
                                 % (token_record.id, user.login, user.id, request.httprequest.url))
                    res = login_and_redirect(request.db, user.login, token_record.name,
                                             redirect_url=request.httprequest.url)

                    # Update the 'new context after login' with fs_ptoken
                    # TODO: Would be much better to use the utm and link_tracker addons
                    if hasattr(request, 'session') and hasattr(request.session, 'context') and request.session.context:
                        request.session.context['fs_ptoken'] = token_record.name
                    return res

        return response
