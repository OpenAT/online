# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.http import request, controllers_per_module
from openerp.tools.mail import html_sanitize

try:
    from premailer import Premailer
except:
    pass

try:
    from html5print import HTMLBeautifier
except:
    pass


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    # ------
    # FIELDS
    # ------
    fso_email_template = fields.Boolean(string='FSON Template')
    fso_template_view_id = fields.Many2one(string='Based on',
                                           comodel_name="ir.ui.view", inverse_name="fso_email_template_ids",
                                           domain="[('fso_email_template','=',True)]")

    fso_email_html = fields.Text(string='E-Mail HTML', compute='_compute_html', compute_sudo=True, store=True,
                                 readonly=True)
    fso_email_html_parsed = fields.Text(string='E-Mail HTML parsed', compute='_compute_html', compute_sudo=True,
                                        store=True, readonly=True)

    @api.depends('body_html', 'fso_template_view_id')
    def _compute_html(self):
        for r in self:
            if r.fso_email_template and r.fso_template_view_id and r.body_html:
                # If i want to call the controller method 'email_preview' directly it would need to:
                # https://www.odoo.com/de_DE/forum/hilfe-1/question/how-to-invoke-a-controller-function-from-inside-a-model-function-87620

                # Render the ir.ui.view qweb template with r.body_html field
                content = r.fso_template_view_id.render({'html_sanitize': html_sanitize,
                                                         'email_editor_mode': False,
                                                         'record': r,
                                                         })
                # Convert from str to unicode
                content = content.decode('utf-8')

                # TODO: Parse Seriendruckfelder

                # Update field
                r.fso_email_html = content

                # Get base_url to replace relative urls with absolute urls
                try:
                    req = request
                    host_url = req.httprequest.host_url
                except Exception as e:
                    host_url = ''
                get_param = self.env['ir.config_parameter'].get_param
                base_url = host_url or get_param('web.freeze.url') or get_param('web.base.url')

                # Inline CSS and set absolute URLs with Premailer
                try:
                    premailer_obj = Premailer(content, base_url=base_url, preserve_internal_links=True,
                                              keep_style_tags=True, strip_important=False, align_floating_images=False,
                                              remove_unset_properties=False, include_star_selectors=False)
                    content = premailer_obj.transform(pretty_print=True)
                except:
                    pass

                # Pretty print html
                try:
                    content = HTMLBeautifier.beautify(content, indent=4)
                except:
                    pass

                # Update field
                r.fso_email_html_parsed = content
