# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request

import datetime

from openerp.tools.mail import html_sanitize
from urllib import urlencode


class FSOEmailEditor(http.Controller):

    # CUSTOM EDITOR SNIPPETS
    # ATTENTION: The Java script call to this json route seems to be bugged or at least 'special' because no kwargs
    #            are accepted by the controller and self is EMPTY therefore we need to get the URL fragments
    #            from request.httprequest.args
    @http.route(['/fso/email/snippets'], type='json', auth="user", website=True)
    def snippets(self):
        snippets_template = str(request.httprequest.values.get('snippets_template', ''))

        return request.website._render(snippets_template)

    # SELECTION PAGE FOR THEMES AND TEMPLATES
    @http.route('/fso/email/select', type='http', auth="user", website=True)
    def email_select(self, **kw):
        """ Overview of email templates to create, edit or copy email templates"""

        # Get E-Mail QWEB Template Views
        template_views = request.env['ir.ui.view'].sudo().search(
            [('fso_email_template', '=', True)], order="write_date DESC")

        # Get E-Mail Templates
        templates = request.env['email.template'].sudo().search([
            ('fso_email_template', '=', True),
            ('fso_template_view_id', '!=', False)], order="write_date DESC")

        odoo_model = kw.pop('odoo_model', '')
        odoo_record_id = kw.pop('odoo_record_id', '')
        if odoo_model and odoo_record_id and kw:
            rec = request.env[odoo_model].browse(int(odoo_record_id))
            rec.write(kw)

        # Render the templates overview page
        return request.render('fso_website_email.fso_email_selection',
                              {'html_sanitize': html_sanitize,
                               'template_views': template_views,
                               'templates': templates,
                               'print_fields': request.env['fso.print_field'].search([]),
                               })

    # EMAIL-EDITOR
    @http.route('/fso/email/edit', type='http', auth="user", website=True)
    def email_edit(self, template_id, **kw):
        template = request.env['email.template'].browse([int(template_id)]) if template_id else False

        if not template or not template.fso_template_view_id:
            return request.redirect('/fso/email/select')

        result = request.render(template.fso_template_view_id.xml_id,
                                {'html_sanitize': html_sanitize,
                                 'email_editor_mode': True,
                                 'record': template,
                                 'print_fields': request.env['fso.print_field'].search([]),
                                 })

        return result

    # E-MAIL PREVIEW (RAW HTML)
    @http.route('/fso/email/preview', type='http', auth="public", website=True)
    def email_preview(self, template_id, raw=True, **kw):
        template = request.env['email.template'].sudo().browse([int(template_id)]) if template_id else False

        if not template or not template.fso_template_view_id:
            return request.redirect('/fso/email/select')

        if raw is True:
            return template.fso_email_html_parsed
        else:
            return request.render(template.fso_template_view_id.xml_id,
                                  {'html_sanitize': html_sanitize,
                                   'email_editor_mode': False,
                                   'record': template,
                                   'print_fields': request.env['fso.print_field'].search([]),
                                   })

    # NEW E-MAIL TEMPLATE FROM THEME OR EXISTING E-MAIL TEMPLATE
    @http.route('/fso/email/create', type='http', auth="user", website=True)
    def email_create(self, template_model,  template_id, **kw):
        if not template_model or not template_id or template_model not in ('email.template', 'ir.ui.view'):
            return request.redirect('/fso/email/select')

        # Theme (ir.ui.view) or email.template id
        template_id = int(template_id)
        # res.partner model id
        ir_model_res_partner_id = request.env['ir.model'].sudo().search([('model', '=', 'res.partner')])[0].id
        # New email.template name
        new_name = datetime.datetime.now().strftime('E-Mail Template (%Y-%m-%d %H:%M:%S)')

        # New e-mail template from theme (ir.ui.view)
        if template_model == 'ir.ui.view':
            theme_view = request.env[template_model].browse([template_id])
            if not theme_view:
                request.redirect('/fso/email/select')
            request.env['email.template'].sudo().create({
                'name': new_name,
                'model_id': ir_model_res_partner_id,
                'fso_email_template': True,
                'fso_template_view_id': theme_view.id,
            })
            return request.redirect('/fso/email/select')

        # Copy existing e-mail template
        if template_model == 'email.template':
            template_to_copy = request.env[template_model].browse([template_id])
            if not template_to_copy:
                request.redirect('/fso/email/select')
            request.env['email.template'].sudo().create({
                'name': new_name,
                'model_id': template_to_copy.model_id.id,
                'fso_email_template': template_to_copy.fso_email_template,
                'fso_template_view_id': template_to_copy.fso_template_view_id.id,
                'body_html': template_to_copy.body_html,
            })
            return request.redirect('/fso/email/select')

        # Return to the e-mail theme/template selection page
        return request.redirect('/fso/email/select')

    # NEW E-MAIL Version
    @http.route('/fso/email/version/create', type='http', auth="user", website=True)
    def email_version_create(self, template_id, **kw):
        if not template_id:
            return request.redirect('/fso/email/select')

        # Get e-mail template
        template = request.env['email.template'].sudo().browse([int(template_id)])

        # Create new version
        template.create_version()

        # Return to the e-mail theme/template selection page
        return request.redirect('/fso/email/edit?template_id='+template_id)

    # NEW E-MAIL Version
    @http.route('/fso/email/version/restore', type='http', auth="user", website=True)
    def email_version_restore(self, template_id, version_id, **kw):
        if not template_id or not version_id:
            return request.redirect('/fso/email/select')

        # Get e-mail template
        template = request.env['email.template'].sudo().browse([int(template_id)])

        # Create new version and restore selected version
        template.restore_version(version_id=version_id)

        # Return to the e-mail theme/template selection page
        return request.redirect('/fso/email/edit?template_id=' + template_id)

    # DELETE E-MAIL TEMPLATE
    @http.route('/fso/email/delete', type='http', auth="user", website=True)
    def email_delete(self,  template_id, **kw):
        if not template_id:
            return request.redirect('/fso/email/select')
        template_id = int(template_id)

        template_to_delete = request.env['email.template'].browse([template_id])
        template_to_delete.unlink()

        return request.redirect('/fso/email/select')
