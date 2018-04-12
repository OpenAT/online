# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request

from openerp.tools.mail import html_sanitize
from urllib import urlencode


class FSOEmailEditor(http.Controller):

    @http.route('/fso/email/select', type='http', auth="user", website=True)
    def email_select(self, **kw):
        """ Overview of email templates to create, edit or copy email templates"""

        # Get E-Mail QWEB Template Views
        template_views = request.env['ir.ui.view'].sudo().search([('fso_email_template', '=', True)])

        # Get E-Mail Templates
        templates = request.env['email.template'].sudo().search([
            ('fso_email_template', '=', True),
            ('fso_template_view_id', '!=', False)])

        # Render the templates overview page
        return request.render('fso_website_email.fso_email_selection',
                              {'html_sanitize': html_sanitize,
                               'template_views': template_views,
                               'templates': templates
                               })

    @http.route('/fso/email/edit', type='http', auth="user", website=True)
    def email_edit(self, template_id, **kw):
        template = request.env['email.template'].browse([int(template_id)]) if template_id else False

        if not template or not template.fso_template_view_id:
            return request.redirect('/fso/email/select')

        result = request.render("fso_website_email.email_designer",
                              {'html_sanitize': html_sanitize,
                               'record': template,
                               'body_field': 'body_html',
                               })

        return result

    @http.route('/fso/email/preview', type='http', auth="user", website=True)
    def email_preview(self, template_id, **kw):
        template = request.env['email.template'].browse([int(template_id)]) if template_id else False

        if not template or not template.fso_template_view_id:
            return request.redirect('/fso/email/select')

        return request.render(template.fso_template_view_id.xml_id,
                              {'html_sanitize': html_sanitize,
                               'record': template,
                               })
