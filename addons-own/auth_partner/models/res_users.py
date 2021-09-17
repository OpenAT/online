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
from openerp import models
from openerp.exceptions import AccessDenied
from openerp.http import request
from openerp.addons.auth_partner.fstoken_tools import fstoken_check

# HINT: http.py:    authenticate > dispatch_rpc() res.users authenticate() >
# HINT: res.users:  authenticate > _login > check_credentials >

class res_users(models.Model):
    _inherit = 'res.users'

    def authenticate(self, db, login, password, user_agent_env):
        res = super(res_users, self).authenticate(db, login, password, user_agent_env)
        return res

    # Extend the check_credentials method to work with FS-Tokens also
    # HINT: check openerp/addons/base/res/res_users.py for more info
    def check_credentials(self, cr, uid, password):
        try:
            # Try regular or other auth methods
            return super(res_users, self).check_credentials(cr, uid, password)
        except AccessDenied:
            # In case there is no request yet (unbound object error catch)
            # https://github.com/OCA/e-commerce/issues/152
            # https://github.com/OCA/e-commerce/pull/190
            if not request:
                raise
            token_record, user_record, errors = fstoken_check(password, store_usage=True)
            if errors:
                raise


