# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.http import request, controllers_per_module
from openerp.tools.mail import html_sanitize

try:
    from bs4 import BeautifulSoup
except:
    pass

try:
    from premailer import Premailer
except:
    pass

# try:
#     from html5print import HTMLBeautifier
# except:
#     pass


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
                # HINT: Will output an UTF-8 encoded str
                content = r.fso_template_view_id.render({'html_sanitize': html_sanitize,
                                                         'email_editor_mode': False,
                                                         'record': r,
                                                         })

                # Update fso_email_html field
                r.fso_email_html = content

                # Parse Print Fields (Seriendruckfelder)
                # http://beautiful-soup-4.readthedocs.io/en/latest/#output
                # HINT: Will auto-detect encoding and concert to unicode
                html_soup = BeautifulSoup(content, "lxml")
                print_fields = html_soup.find_all(class_="drop_in_print_field")
                for pf in print_fields:
                    pf_class = [c for c in pf.get("class", []) if c.startswith("pf_")]
                    pf_span = pf.find_all(class_=pf_class[0])
                    fs_string = pf_span[0].get("data-fs-email-placeholder")
                    pf.replace_with(fs_string)
                # Output html in unicode and keep most html entities (done by formatter="minimal")
                content = html_soup.prettify(formatter="minimal")

                # Get base_url to replace relative urls with absolute urls
                try:
                    req = request
                    host_url = req.httprequest.host_url
                except Exception as e:
                    host_url = ''
                get_param = self.env['ir.config_parameter'].get_param
                base_url = host_url or get_param('web.freeze.url') or get_param('web.base.url')

                # Inline CSS and set absolute URLs with Premailer
                premailer_obj = Premailer(content, base_url=base_url, preserve_internal_links=True,
                                          keep_style_tags=True, strip_important=False, align_floating_images=False,
                                          remove_unset_properties=False, include_star_selectors=False)
                content = premailer_obj.transform(pretty_print=True)

                # Pretty print html
                # try:
                #     content = HTMLBeautifier.beautify(content, indent=4)
                # except:
                #     pass

                # Update fso_email_html_parsed field
                r.fso_email_html_parsed = content
