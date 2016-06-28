# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


class WebsitePopUp(http.Controller):

    @http.route("/website_popup/cancel", auth="public")
    def popup_cancel(self, redirect="/"):
        """Hide/Cancel the PopUp Box for this Session"""
        request.session["website_popup_cancel"] = True
        return http.local_redirect(redirect)

    @http.route("/website_popup/enable", auth="public")
    def popup_enable(self, redirect="/"):
        """Enable the PopUp Box"""
        request.session["website_popup_cancel"] = False
        return http.local_redirect(redirect)

    @http.route("/website_popup/edit", type='http', auth="public", website=True)
    def popup_edit(self, **post):
        """Edit the PopUp Box Content"""
        request.session["website_popup_cancel"] = True
        return request.website.render("website_popup.popupbox_edit", post)
