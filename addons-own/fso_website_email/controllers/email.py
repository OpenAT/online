# -*- coding: utf-8 -*-

from openerp.addons.web import http
from openerp.http import request
from openerp.tools.mail import html_sanitize

from urllib import urlencode


class FSOWebsiteEmailDesigern(http.Controller):

    @http.route('/fso/email_designer', type='http', auth="user", website=True)
    def index(self, model, res_id, template_model=None, **kw):
        # http://demo.local.com/website_mail/email_designer?model=email.template&res_id=1&return_action=584&

        # Redirect if parameter are missing
        if not model or not model in request.registry or not res_id:
            return request.redirect('/')

        # Redirect if fields are missing in given model
        model_fields = request.registry[model]._fields
        if 'body' not in model_fields and 'body_html' not in model_fields or \
                'email' not in model_fields and 'email_from' not in model_fields or \
                'name' not in model_fields and 'subject' not in model_fields:
            return request.redirect('/')

        # Get the related record(set)
        res_id = int(res_id)

        # Redirect if record does not exist
        obj_ids = request.registry[model].exists(request.cr, request.uid, [res_id], context=request.context)
        if not obj_ids:
            return request.redirect('/')

        # Set fields from record
        # HINT: since t-field is static we have to do this field by field
        email_from_field = 'email'
        if 'email_from' in model_fields:
            email_from_field = 'email_from'
        subject_field = 'name'
        if 'subject' in model_fields:
            subject_field = 'subject'
        body_field = 'body'
        if 'body_html' in model_fields:
            body_field = 'body_html'

        # Get db cursor, user ID and context from current request
        cr, uid, context = request.cr, request.uid, request.context
        record = request.registry[model].browse(cr, uid, res_id, context=context)

        # Set values dict for template rendering
        values = {
            'record': record,
            'templates': None,
            'model': model,
            'res_id': res_id,
            'email_from_field': email_from_field,
            'subject_field': subject_field,
            'body_field': body_field,
            'return_action': kw.get('return_action', ''),
        }

        # Start the e-mail designer
        if getattr(record, body_field):
            values['mode'] = 'email_designer'
        # List e-mail templates to choose one as a start
        else:
            if kw.get('enable_editor'):
                kw.pop('enable_editor')
                fragments = dict(model=model, res_id=res_id, **kw)
                if template_model:
                    fragments['template_model'] = template_model
                return request.redirect('/fso/email_designer?%s' % urlencode(fragments))
            values['mode'] = 'email_template'

        # Get all e-mail templates for the given template_model
        tmpl_obj = request.registry['email.template']
        if template_model:
            tids = tmpl_obj.search(cr, uid, [('model', '=', template_model)], context=context)
        # If no template model is given get all all e-mail templates
        else:
            tids = tmpl_obj.search(cr, uid, [], context=context)
        templates = tmpl_obj.browse(cr, uid, tids, context=context)
        values['templates'] = templates

        # Add the html_sanitize function to the xml-template to be used in qweb
        values['html_sanitize'] = html_sanitize

        # Render the template and return the website
        return request.website.render("fso_website_email.email_designer", values)

    @http.route('/fso/email_designer/preview', type='http', auth="user", website=True)
    def email_preview(self, res_id, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        # http://demo.local.com/fso/email_designer/preview?res_id=1

        model = 'email.template'
        res_id = int(res_id)
        record = request.registry[model].browse(cr, uid, res_id, context=context)

        values = {
            'record': record,
        }

        return request.website.render("fso_website_email.email_preview", values)

    # @http.route(['/website_mail/snippets'], type='json', auth="user", website=True)
    # def snippets(self):
    #     return request.website._render('website_mail.email_designer_snippets')
