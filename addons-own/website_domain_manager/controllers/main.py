# -*- coding: utf-8 -*-
from openerp import models
from openerp.http import request
from openerp.tools.translate import _

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        # ATTENTION: _dispatch() must called before anything else!
        # TODO: Find a better "entry point" then _dispatch() for WebRequests
        dispatch = super(IrHttp, self)._dispatch()

        if not hasattr(request, 'httprequest') or not request.httprequest.host \
                or not hasattr(request, 'website') or not request.website:
            return dispatch

        # Get current request domain without port
        request_domain = request.httprequest.host.split(':', 1)[0]
        domains = request.env['website.website_domains']

        # Search if a website.website_domain with inactive template exits for current request domain
        domain_set = domains.sudo().search(['&',
                                           ('domain', '=', request_domain),
                                           ('template.active', '=', False)])

        # Deactivate templates if
        # 1.) a website domain with deactivated template was found for the request_domain
        # 2.) no website template domain was found for the request_domain
        if domain_set or not domains.sudo().search([('domain', '=', request_domain)]):
            views = request.env['ir.ui.view'].search(['&', '&',
                                                      ('active', '=', True),
                                                      ('type', '=', 'qweb'),
                                                      ('model_data_id.name', '=like', '%website_domain_template%')])
            views.sudo().write({'active': False})

        # Activated website domain template
        if domain_set:
            assert domain_set.ensure_one(), _("Request domain %s found multiple times "
                                              "in website.website_domains" % request_domain)
            # Activate the domain template
            domain_set[0].template.active = True

        # Finish the request
        return dispatch

