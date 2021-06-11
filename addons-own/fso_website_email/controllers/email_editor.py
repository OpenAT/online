# -*- coding: utf-8 -*-
import werkzeug
import datetime
import urllib
from urllib import urlencode

from openerp import http
from openerp.http import request
from openerp.tools.mail import html_sanitize


class QueryURL(object):
    def __init__(self, path='', **args):
        self.path = path
        self.args = args

    def __call__(self, path=None, **kw):
        if not path:
            path = self.path
        for k,v in self.args.items():
            kw.setdefault(k,v)
        l = []
        for k,v in kw.items():
            if v:
                if isinstance(v, list) or isinstance(v, set):
                    l.append(werkzeug.url_encode([(k,i) for i in v]))
                else:
                    l.append(werkzeug.url_encode([(k,v)]))
        if l:
            path += '?' + '&'.join(l)
        return path


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
    @http.route(['/fso/email/select',
                 '/fso/email/select/page/<int:page>'],
                type='http', auth="user", website=True)
    def email_select(self, page=0, search='', **kw):
        """ Overview of email templates to create, edit or copy email templates"""

        keep = QueryURL('/fso/email/select', search=search)

        # Update the e-mail template (email.template) or the theme (ir.ui.view)
        # HINT: This is used for name or theme changes right now
        odoo_model = kw.pop('odoo_model', '')
        odoo_record_id = kw.pop('odoo_record_id', '')
        if odoo_model and odoo_record_id and kw:
            rec = request.env[odoo_model].browse(int(odoo_record_id))
            changed_fields = {k: v for k, v in kw.iteritems() if v != unicode(getattr(rec[k], 'id', rec[k]))}
            if changed_fields:
                rec.write(changed_fields)

        # Get E-Mail Themes (ir.ui.view QWEB Template Views)
        template_views = request.env['ir.ui.view'].sudo().search(
            [('fso_email_template', '=', True)], order="write_date DESC")

        # Get E-Mail Template object
        template_obj = request.env['email.template'].sudo()

        # E-Mail template domain
        template_domain = [('fso_email_template', '=', True),
                           ('fso_template_view_id', '!=', False)]

        if search and hasattr(template_obj, 'sosync_fs_id'):
            # Include sosync_fs_id in search, if it exists
            template_domain += ['|',
                                '|',
                                ('name', 'ilike', search),
                                ('id', '=', search),
                                ('sosync_fs_id', '=', search)]
        elif search:
            template_domain += ['|',
                                ('name', 'ilike', search),
                                ('id', '=', search)]

        # Order by
        # template_order = "write_date DESC"
        template_order = "create_date DESC"

        # Pager for email templates
        templates_per_page = 12
        url = '/fso/email/select'
        template_count = template_obj.search_count(template_domain)
        pager = request.website.pager(url=url,
                                      total=template_count,
                                      page=page,
                                      step=templates_per_page,
                                      scope=8,
                                      url_args=kw)
        templates = template_obj.search(template_domain,
                                        limit=templates_per_page,
                                        offset=pager['offset'],
                                        order=template_order)

        # Render the templates overview page
        return request.render('fso_website_email.fso_email_selection',
                              {'html_sanitize': html_sanitize,
                               'template_views': template_views,
                               'pager': pager,
                               'templates': templates,
                               'print_fields': request.env['fso.print_field'].search([]),
                               'return_url': urllib.unquote(kw.get('return_url', '')),
                               'search': search,
                               'keep': keep,
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
                                 'return_url': urllib.unquote(kw.get('return_url', '')),
                                 })

        return result

    # E-MAIL PREVIEW (RAW HTML)
    @http.route('/fso/email/preview', type='http', auth="public", website=True)
    def email_preview(self, template_id, raw=True, fso_email_html=False, **kw):
        template = request.env['email.template'].sudo().browse([int(template_id)]) if template_id else False

        if not template or not template.fso_template_view_id:
            return request.redirect('/fso/email/select')

        if fso_email_html:
            return template.fso_email_html

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
            return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw) or '')

        # Copy existing e-mail template
        if template_model == 'email.template':
            template_to_copy = request.env[template_model].browse([template_id])
            if not template_to_copy:
                return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw))
            request.env['email.template'].sudo().create({
                'name': new_name,
                'model_id': template_to_copy.model_id.id,
                'fso_email_template': template_to_copy.fso_email_template,
                'fso_template_view_id': template_to_copy.fso_template_view_id.id,
                'body_html': template_to_copy.body_html,
            })
            return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw))

        # Return to the e-mail theme/template selection page
        return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw))

    # NEW E-MAIL Version
    @http.route('/fso/email/version/create', type='http', auth="user", website=True)
    def email_version_create(self, template_id, **kw):
        if not template_id:
            return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw))

        # Get e-mail template
        template = request.env['email.template'].sudo().browse([int(template_id)])

        # Create new version
        template.create_version()

        # Return to the e-mail theme/template selection page
        return request.redirect('/fso/email/edit?template_id='+template_id+'&'+urllib.urlencode(kw))

    # NEW E-MAIL Version
    @http.route('/fso/email/version/restore', type='http', auth="user", website=True)
    def email_version_restore(self, template_id, version_id, **kw):
        if not template_id or not version_id:
            return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw))

        # Get e-mail template
        template = request.env['email.template'].sudo().browse([int(template_id)])

        # Create new version and restore selected version
        template.restore_version(version_id=version_id)

        # Return to the e-mail theme/template selection page
        return request.redirect('/fso/email/edit?template_id='+template_id+'&'+urllib.urlencode(kw))

    # DELETE E-MAIL TEMPLATE
    @http.route('/fso/email/delete', type='http', auth="user", website=True)
    def email_delete(self,  template_id, **kw):
        if not template_id:
            return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw))
        template_id = int(template_id)

        template_to_delete = request.env['email.template'].browse([template_id])

        # Do not really delete the template but "hide" it
        if template_to_delete:
            template_to_delete.write({'active': False})

        return request.redirect('/fso/email/select?%s' % urllib.urlencode(kw))
