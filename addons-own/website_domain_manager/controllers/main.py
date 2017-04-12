# -*- coding: utf-8 -*-
from openerp import models
from openerp.http import request
from openerp.tools.translate import _

# HINT: to inherit from _dispatch() was found at addons/crm/ir_http.py
class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        # ATTENTION: _dispatch() must called before anything else!
        dispatch = super(IrHttp, self)._dispatch()

        # Return if there is not (jet) an env or this is not a httprequest or website request (e.g.: a backend request)
        if not hasattr(request, 'env') or not request.env \
                or not hasattr(request, 'httprequest') or not request.httprequest.host \
                or not hasattr(request, 'website') or not request.website:
            return dispatch

        request_domain = request.httprequest.host.split(':', 1)[0]
        domains = request.env['website.website_domains']

        # DOMAIN REDIRECT
        # Store the domain redirect url in the session to redirect by js if not opened in an iframe (see templates.xml)
        redirect = domains.sudo().search(['&',
                                         ('name', '=', request_domain),
                                         ('redirect_url', '!=', False)])
        if redirect:
            request.session['noiframe_redirect_url'] = redirect[0].redirect_url
        else:
            request.session.pop('noiframe_redirect_url', False)

        # DOMAIN TEMPLATE
        # Search if a website.website_domain with an INACTIVE template exits for current request domain
        domain_set = domains.sudo().search(['&',
                                           ('name', '=', request_domain),
                                           ('template.active', '=', False)])

        # Search and deactivate other website domain templates if:
        # a.) A website domain with deactivated template was found for the requested domain (= deactivate former wdt)
        # b.) No website template domain was found for the request_domain (= deactivate all website domain templates)
        # c.) TODO: what if all templates are active at first run
        if domain_set or not domains.sudo().search([('name', '=', request_domain)]):
            views = request.env['ir.ui.view'].sudo().search(['&',
                                                            ('active', '=', True),
                                                            ('id', 'in', domains.get_domain_template_ids())])
            # ATTENTION: Do not use .write({}) here to avoid concurrent writes!
            for view in views:
                view.sudo().active = False

        # Activated website domain template for the request url
        if domain_set:
            # Activate the domain template
            domain_set[0].sudo().template.active = True

        # FINISH the request
        return dispatch
