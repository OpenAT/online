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

# !!! DISABLE BECAUSE DIRECTLY DONE IN SIMPLE CHECKOUT !!!

# from openerp.http import request
# from openerp.osv import orm
#
#
# class ir_http(orm.AbstractModel):
#     _inherit = 'ir.http'
#
#     def _dispatch(self):
#         response = super(ir_http, self)._dispatch()
#
#         if request.website:
#             if 'fs_ptoken' in request.httprequest.args:
#                 # Check if the token exists
#                 # TODO: Check if the token is valid
#                 fstoken_obj = request.env['res.partner.fstoken']
#                 fstoken = fstoken_obj.search([('name', '=', request.httprequest.args['fs_ptoken'])], limit=1)
#                 # Add related res.partner from the token to the session if we are not logged in
#                 if fstoken and request.website.user_id.id == request.env.uid:
#                     request.session['fs_ptoken_user_id'] = fstoken.partner_id.id
#
#         return response
