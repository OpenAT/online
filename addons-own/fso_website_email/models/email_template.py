# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.tools.mail import html_sanitize
from openerp.exceptions import ValidationError
from openerp.http import request, controllers_per_module
from openerp.addons.fso_base.tools.validate import is_valid_email
from openerp.addons.fso_base.tools.image import screenshot

import datetime
import os
import tempfile
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

import logging
logger = logging.getLogger(__name__)


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    @api.model
    def get_base_url(self):
        # Get base_url to replace relative urls with absolute urls
        try:
            req = request
            host_url = req.httprequest.host_url
        except Exception as e:
            host_url = ''
        get_param = self.env['ir.config_parameter'].get_param
        base_url = host_url or get_param('web.freeze.url') or get_param('web.base.url')
        return base_url

    # ------
    # FIELDS
    # ------
    active = fields.Boolean(string="Active", default=True)

    # Mark this as an FSON E-Mail Template and link Theme (ir.ui.view)
    fso_email_template = fields.Boolean(string='FSON Template')
    fso_template_view_id = fields.Many2one(string='Based on',
                                           comodel_name="ir.ui.view", inverse_name="fso_email_template_ids",
                                           domain="[('fso_email_template','=',True)]")

    # Compute final html
    fso_email_html = fields.Text(string='E-Mail HTML', compute='_compute_html', store=True,
                                 readonly=True, translate=True)
    fso_email_html_parsed = fields.Text(string='E-Mail HTML parsed', compute='_compute_html', store=True,
                                        readonly=True, translate=True)
    screenshot = fields.Binary(string="Screenshot", compute='_compute_html', store=True,
                               readonly=True)

    # Store Versions (copies of email.template)
    # HINT: version_ids will be empty because One2Many will not show inactive records but it is still here for
    #       completeness
    version_ids = fields.One2many(comodel_name="email.template", inverse_name="version_of_email_id",
                                  string='Available Versions')

    version_of_email_id = fields.Many2one(comodel_name="email.template", inverse_name="version_ids",
                                          string='Version of')

    @api.constrains('email_from', 'reply_to')
    def _constrain_email_address(self):
        for r in self:
            if r.email_from and not is_valid_email(r.email_from):
                raise ValidationError(_("Field 'email_from' contains no valid e-mail address!"))
            if r.reply_to and not is_valid_email(r.reply_to):
                raise ValidationError(_("Field 'reply_to' contains no valid e-mail address!"))

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
                                                         'debug': 'assets',
                                                         })

                # Get the base url of current request or from ir.config parameters
                base_url = self.get_base_url()

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

                # # DISABLED: Repair style <link> tags for premailer for theme assets
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

                # Try to generate a screenshot
                tmp = tempfile.NamedTemporaryFile(bufsize=0, suffix=".html", delete=True)
                try:
                    tmp.write(content.encode(encoding='utf-8'))
                    screenshot_url = 'file://'+tmp.name
                    screenshot_img = screenshot(screenshot_url,
                                                src_width=1024, src_height=1181, tgt_width=260, tgt_height=300)
                    r.screenshot = screenshot_img or False
                except Exception as e:
                    logger.error("Could not create screenshot for e-mail template:\n%s" % repr(e))
                    r.screenshot = False
                finally:
                    tmp.close()

    @api.multi
    def write(self, values):
        # ATTENTION: After this 'self' is changed (in memory i guess) 'res' is only a boolean
        res = super(EmailTemplate, self).write(values)

        # Immediately submit the related sync job for FRST e-mail templates
        for r in self:
            if r.fso_email_template and r.fso_template_view_id and r.body_html:
                try:
                    sync_job = self.env['sosync.job.queue'].sudo().search([
                        ('job_source_system', '=', 'fso'),
                        ('job_source_model', '=', 'email.template'),
                        ('job_source_record_id', '=', r.id),
                        ('submission_state', '=', 'new'),
                    ], limit=1)
                    if sync_job:
                            sync_job.submit_sync_job()
                except Exception as e:
                    logger.error("Immediate sync_job submission failed!\n%s" % repr(e))
                    pass

    @api.multi
    def create_version(self, version_name=''):
        assert self.ensure_one(), _("E-Mail Template Versions can only be created for a single E-Mail Template")
        r = self
        version_name = version_name or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        version = r.copy(default={
            'active': False,
            'name': version_name,
            'version_ids': False,
            'version_of_email_id': r.id,
        })
        # Hack because 'name' will always be set by copy even if in default dict
        version.name = version_name
        return version

    @api.multi
    def restore_version(self, version_id=False):
        assert self.ensure_one(), _("E-Mail Template Versions can only be restored for a single E-Mail Template")
        assert not self.version_of_email_id, _("You can not restore a version of a version!")

        # ATTENTION: Non active records are not shown in version_ids therefore it appears empty
        #assert version_id in self.version_ids.ids, _("Version is not a Version of this E-Mail Template")

        r = self

        # Find the version
        version = self.sudo().browse([int(version_id)])
        assert version, _("Version to restore was not found!")
        assert version.version_of_email_id.id == r.id, _("Version is not a Version of this E-Mail Template")

        # Get data to restore
        data_to_restore = version.copy_data()[0]

        # Exclude fields that should not be restored
        # TODO: ADD the sosync field to the MAGIC_COLUMNS in models.py in fso_sosync so they will not be
        #       copied by default :)
        data_to_restore = {key: value for (key, value) in data_to_restore.items() if key not in (
            'active', 'name', 'version_of_email_id', 'version_ids',
            'sosync_write_date', 'sosync_sync_date', 'sosync_fs_id')}

        # Create a new version from current data first
        assert r.create_version(), _("Could not create a version of the email template before restore!")

        # Update email template
        r.sudo().write(data_to_restore)

        return True
