# -*- coding: utf-8 -*-

from openerp.http import request
from openerp.osv import orm
from openerp.addons.auth_partner.fstoken_tools import fstoken


# add fs_ptoken to the session if in URL or post args
class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        response = super(ir_http, self)._dispatch()

        if hasattr(request, 'website'):
            # CHECK for fs_ptoken in any URL to make a valid token permanent for this session
            #       (Valid tokens of the fs_ptoken in the request.session['valid_fstoken'])
            # HINT: The _dispatch() method will run LAST so there is a good chance fstoken() was already called
            # HINT: This will not get fs_ptoken from form submissions but just from URIs
            fs_ptoken = request.httprequest.args.get('fs_ptoken')
            if fs_ptoken and fs_ptoken != request.session.get('valid_fstoken', ''):
                # CHECK TOKEN
                # HINT: This will also store the token to request.session['valid_fstoken'] if token is valid
                fstoken(fs_ptoken=fs_ptoken)

        return response
