# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.tools.mail import html_sanitize

from openerp.http import request, controllers_per_module
#from openerp.addons.web.http import request

from openerp.addons.fso_website_email.controllers.email_editor import FSOEmailEditor

import requests


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

                # TODO: Change this to an URL CALL of preview !!!
                # Render the ir.ui.view qweb template with r.body_html field
                # HINT: Will output an UTF-8 encoded str
                content = r.fso_template_view_id.render({'html_sanitize': html_sanitize,
                                                         'email_editor_mode': False,
                                                         'record': r,
                                                         'debug': 'assets',
                                                         })

                # Get base_url to replace relative urls with absolute urls
                try:
                    req = request
                    host_url = req.httprequest.host_url
                except Exception as e:
                    host_url = ''
                get_param = self.env['ir.config_parameter'].get_param
                base_url = host_url or get_param('web.freeze.url') or get_param('web.base.url')
                # print "base_url %s" % base_url

                # response = requests.get(base_url.rstrip('/') +
                #                         '/fso/email/preview?template_id=' +
                #                         str(r.fso_template_view_id.id))

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

                # Repair anchors <a> (e.g.: www.google.at > https://www.google.at)
                anchors = html_soup.find_all('a')
                for a in anchors:
                    href = a.get('href', '').strip()
                    href = href if '://' not in href else ''
                    if href and not (
                            href.startswith('#') or href.startswith('/') or
                            href.startswith('http') or href.startswith('mailto')):
                        a['href'] = 'https://'+href

                # # Repair style <link> tags for premailer for theme assets
                # stylesheets = html_soup.find_all('link')
                # base_url_no_slash = base_url.rstrip('/')
                # for link in stylesheets:
                #     if 'stylesheet' in link.get('rel', '') and not link.get('type', '').strip():
                #         link['type'] = 'text/css'
                #         href = link.get('href', '').strip()
                #         if 'web/css' in href:
                #             link['href'] = base_url_no_slash + href
                #             print link['href']

                # Output html in unicode and keep most html entities (done by formatter="minimal")
                content = html_soup.prettify(formatter="minimal")

                # Update fso_email_html field
                r.fso_email_html = content

                # Inline CSS and convert relative to absolute URLs with premailer
                premailer_obj = Premailer(content, base_url=base_url, preserve_internal_links=True,
                                          keep_style_tags=True, strip_important=False, align_floating_images=False,
                                          remove_unset_properties=False, include_star_selectors=False)
                content = premailer_obj.transform(pretty_print=True)

                # Convert URLS to "ranner multimailer" tracking URLS
                # Target Example: %redirector%/https//www.global2000.at/ceta-verhindern
                html_soup = BeautifulSoup(content, "lxml")
                anchors = html_soup.find_all('a')
                for a in anchors:
                    href = a.get('href', '').strip()
                    href = href if '://' in href else ''
                    if href and href.startswith('http') and 'dadi_notrack' not in a.get('class', ''):
                        protocol, address = href.split('://', 1)
                        a['href'] = '%redirector%/' + protocol + '//' + address

                # Output html in unicode and keep most html entities (done by formatter="minimal")
                content = html_soup.prettify(formatter="minimal")

                # DISABLED: Pretty print html, css and js
                # try:
                #     content = HTMLBeautifier.beautify(content, indent=4)
                # except:
                #     pass

                # Update fso_email_html_parsed field
                r.fso_email_html_parsed = content