# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class FrstZgruppeController(http.Controller):

    @http.route('/frst/group/approve', type='http', auth="public", website=True)
    def frst_group_approve(self, group_approve_fson_zgruppedetail_id=None, **post):
        try:
            zgruppedetail_id = int(group_approve_fson_zgruppedetail_id)
        except Exception as e:
            zgruppedetail_id = None
        if zgruppedetail_id:
            zgruppedetail = request.env['frst.zgruppedetail'].sudo().search([('id', '=', zgruppedetail_id)])
        else:
            zgruppedetail = None
        return request.website.render('fso_frst_groups_email.frst_group_approve', {'zgruppedetail': zgruppedetail})
