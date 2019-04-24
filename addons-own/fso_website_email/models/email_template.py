# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools, registry
from openerp.tools.translate import _
from openerp.tools.mail import html_sanitize
from openerp.exceptions import ValidationError
from openerp.http import request, controllers_per_module
from openerp.addons.fso_base.tools.validate import is_valid_email
from openerp.addons.fso_base.tools.image import screenshot

import re
import cssutils

import datetime
import tempfile
import os
from urlparse import urlparse

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
import requests

import logging
logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except Exception as e:
    logger.error("Import bs4 (BeautifulSoup) error!\n%s" % repr(e))
    pass

try:
    from premailer import Premailer
    # Premailer logging
    from io import StringIO
    premailer_log = StringIO()
    premailer_log_handler = logging.StreamHandler(premailer_log)
except Exception as e:
    logger.error("Import premailer error!\n%s" % repr(e))
    pass


# Create an adapter for requests that will use TLSv1 (and not sslv2 which is insecure and disabled in most webservers)
# TODO: Make sure request uses TLSv1 and not SSL v2.x
#       https://lukasa.co.uk/2017/02/Configuring_TLS_With_Requests/
#       https://lukasa.co.uk/2013/01/Choosing_SSL_Version_In_Requests/
#       https://stackoverflow.com/questions/14102416/python-requests-requests-exceptions-sslerror-errno-8-ssl-c504-eof-occurred
class RequestsTLSv1Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1,
                                       **pool_kwargs)


# Override premailer method to set timeout for requests and TLS v1 as SSL protocol
class PremailerWithTimeout(Premailer):
    def _load_external_url(self, url):
        logger.info("Premailer get url with timeout: %s" % url)

        # Start a new session and mount the TLSv1 Adapter
        s = requests.Session()
        s.mount(url, RequestsTLSv1Adapter())

        # Get the url with timeout
        res = s.get(url, timeout=14.0)
        return res.text


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

    # Mark this email.template as a FSON e-mail template
    fso_email_template = fields.Boolean(string='FSON Template')

    # Link an 'ir.ui.view' as the theme for this email.template
    fso_template_view_id = fields.Many2one(string='Based on',
                                           comodel_name="ir.ui.view", inverse_name="fso_email_template_ids",
                                           domain="[('fso_email_template','=',True)]",
                                           #default=lambda self: self.env.ref('fso_website_email.theme_dadi'), # will not work on install :(
                                           )

    # COMPUTED IN 'create' AND 'write' METHODS
    # ----------------------------------------
    # Compute e-mail HTML-code based on the theme (ir.ui.view) and this e-mail template
    fso_email_html = fields.Text(string='E-Mail body FSON',
                                 readonly=True, translate=True,
                                 help="E-Mail body HTML code with Fundraising Studio print field placeholders!\n"
                                      "  - https:// added to href targets if missing\n"
                                      "  - absolute urls based on self.get_base_url()\n"
                                      "  - inline css\n"
                                      "  - print fields html replaced with FRST print fields placeholders")

    # Compute e-mail HTML-code with tracked, absolute URL's and correct code for print fields for Fundraising Studio.
    # HINT: Should be called fso_email_html_tracked but now it's not worth the change :)
    fso_email_html_parsed = fields.Text(string='E-Mail body FRST-Multimailer',
                                        readonly=True, translate=True,
                                        help="E-Mail body HTML to be used by Fundraising Studio 'Multimailer'!\n"
                                             " - URL's rewritten to FRST-Multimailer format\n")

    # Compute e-mail screenshot
    screenshot = fields.Binary(string="Screenshot", readonly=True, translate=False)
    screenshot_pending = fields.Boolean(string="Screenshot pending", readonly=True,
                                        help="Indicates that a screenshot must be rendered in the background")

    # VERSION HANDLING
    # ----------------
    # Store Versions (copies of email.template)
    # HINT: version_ids will be empty because One2Many will not show inactive records but it is still here for
    #       completeness
    version_ids = fields.One2many(comodel_name="email.template", inverse_name="version_of_email_id",
                                  string='Available Versions')

    version_of_email_id = fields.Many2one(comodel_name="email.template", inverse_name="version_ids",
                                          string='Version of')

    # -------------------------
    # CONSTRAINS AND VALIDATION
    # -------------------------
    @api.constrains('email_from', 'reply_to')
    def _constrain_email_address(self):
        for r in self:
            if r.email_from and not is_valid_email(r.email_from):
                raise ValidationError(_("Field 'email_from' contains no valid e-mail address!"))
            if r.reply_to and not is_valid_email(r.reply_to):
                raise ValidationError(_("Field 'reply_to' contains no valid e-mail address!"))

    # -------
    # METHODS
    # -------
    @api.multi
    def _update_fson_html_fields_and_screenshot_pending(self):

        for rec in self:

            # Skipp this for email_template versions
            if rec.version_of_email_id:
                continue

            # Update fields 'fso_email_html', 'fso_email_html_parsed' and 'screenshot_pending'
            logger.info("Update fields 'fso_email_html', 'fso_email_html_parsed' and 'screenshot_pending' "
                        "for email.template with id %s" % rec.id)

            # Only update fields if all needed fields are set
            if rec.fso_email_template and rec.fso_template_view_id and rec.body_html:

                # Render the the related theme (ir.ui.view) to get the basic html content of the email body
                email_body = rec.fso_template_view_id.render({'html_sanitize': html_sanitize,
                                                              'email_editor_mode': False,
                                                              'record': rec,
                                                              'print_fields': self.env['fso.print_field'].search([]),
                                                              })

                # Convert html content to a beautiful soup object
                email_body_soup = BeautifulSoup(email_body, "lxml")

                # Replace print fields in e-mail body html with correct code for Fundraising Studio
                # HINT: http://beautiful-soup-4.readthedocs.io/en/latest/#output
                # HINT: Will auto-detect encoding and convert to unicode
                # HINT: 'class_' is used by html_soup because 'class' is a reserved keyword in python
                email_body_soup_print_fields = email_body_soup.find_all(class_="drop_in_print_field")
                for pf in email_body_soup_print_fields:
                    pf_class = [c for c in pf.get("class", []) if c.startswith("pf_")]
                    pf_span = pf.find_all(class_=pf_class[0])
                    fs_string = pf_span[0].get("data-fs-email-placeholder")
                    pf.replace_with(fs_string)

                # Repair anchors without protocol
                # E.g.: www.google.at > https://www.google.at
                email_body_soup_anchors = email_body_soup.find_all('a')
                for a in email_body_soup_anchors:
                    href = a.get('href', '').strip()
                    if '://' in href or any(href.startswith(x) for x in ('http', 'mailto', '/', '#', '%')):
                        continue
                    else:
                        a['href'] = 'https://' + href

                # Convert beautiful soup object to regular html
                # HINT: keep html entities like &nbsp; by using the formater "html" instead of "minimal"
                email_body_prepared = email_body_soup.prettify(formatter="html")

                # Use premailer to:
                #  - inline CSS and
                #  - convert relative to absolute URLs
                # HINT: This step must done before generatig multimailer links
                # ATTENTION: This step will try a lot of requests.packages.urllib3.connectionpool connections
                #            which may lead to long processing times.
                email_body_prepared_premailer = PremailerWithTimeout(email_body_prepared,
                                                                     method='xml',
                                                                     base_url=self.get_base_url(),
                                                                     preserve_internal_links=True,
                                                                     keep_style_tags=False,
                                                                     strip_important=True,
                                                                     align_floating_images=False,
                                                                     remove_unset_properties=True,
                                                                     include_star_selectors=False,
                                                                     cssutils_logging_handler=premailer_log_handler,
                                                                     cssutils_logging_level=logging.FATAL,)
                fso_email_html = email_body_prepared_premailer.transform(pretty_print=True)

                # Convert html content to a beautiful soup object again
                email_body_css_inline_soup = BeautifulSoup(fso_email_html, "lxml")

                # Replace anchors with FRST-Multimailer links
                email_body_css_inline_soup_anchors = email_body_css_inline_soup.find_all('a')
                for a in email_body_css_inline_soup_anchors:
                    href = a.get('href', '').strip()
                    # Handle and fix '%open_browser%' FRST-Multimailer links
                    if '%open_browser%' in href:
                        a['href'] = '%open_browser%'
                        continue
                    # Multimailer Token-Links: Add ?fs_ptoken=%xGuid% to token links for FRST
                    if 'link-withtoken' in a.get('class', ''):
                        token_query = '&fs_ptoken=%xGuid%' if '?' in href else '?fs_ptoken=%xGuid%'
                        href = href+token_query
                        a['href'] = href
                        logger.info("TOKEN QUERY %s " % href)
                    # Skipp rewrite to tracking link if 'link-donottrack' class is set
                    if 'link-donottrack' in a.get('class', ''):
                        continue
                    # Convert to FRST-Multimailer link
                    if '://' in href and href.startswith('http'):
                        protocol, address = href.split('://', 1)
                        a['href'] = '%redirector%/' + protocol + '//' + address

                def cycle_rules(rules):
                    for r in rules:
                        if r.type == r.STYLE_RULE:
                            for p in r.style:
                                p.priority = 'IMPORTANT'
                        elif hasattr(r, 'cssRules'):
                            cycle_rules(r)

                # Add important to all CSS tags
                # HINT: Only the media queries will be left over in the style tags
                for styletag in email_body_css_inline_soup.find_all('style'):
                    css = styletag.string
                    css_parsed = cssutils.parseString(css, validate=True)
                    cycle_rules(css_parsed)
                    styletag.string = css_parsed.cssText

                # Convert beautiful soup object back to regular html
                fso_email_html_parsed = email_body_css_inline_soup.prettify(formatter="html")

                # Update the email.template fields
                return rec.write({'fso_email_html': fso_email_html,
                                  'fso_email_html_parsed': fso_email_html_parsed,
                                  'screenshot': False,
                                  'screenshot_pending': True})

            # Make sure all fields are unset if any of the mandatory fields are missing
            else:
                if any(rec[f] for f in ['fso_email_html', 'fso_email_html_parsed', 'screenshot']):
                    return rec.write({'fso_email_html': False,
                                      'fso_email_html_parsed': False,
                                      'screenshot': False,
                                      'screenshot_pending': False})

    @api.multi
    def screenshot_update(self, src_width=1024, src_height=1181, tgt_width=260, tgt_height=300):
        logger.info("START to generate screenshots for email.templates with ids %s !" % self.ids)

        # CHECK LANGUAGE SETTINGS OF CONTEXT AND USER!
        context = self.env.context
        context_lang = context.get('lang', False)
        user = self.env.user
        if not context_lang:
            logger.warning('screenshot_update() No language set in context! '
                           'Language of request user "%s" with id "%s" is "%s"' % (user.name, user.id, user.lang))
            if user.lang:

                # Check if the users language is the same as the default website language!
                website = self.env['website'].sudo().browse([1])[0]
                website_default_lang = website.default_lang_id.code
                if website_default_lang != user.lang:
                    logger.warning('screenshot_update() Language "%s" of request user is NOT the '
                                   'default website language "%s"' % (user.lang, website_default_lang))

                # Update the context to the user lang
                logger.warning('screenshot_update() switching context language to %s' % user.lang)
                context_temp = dict(context)
                context_temp.update({'lang': user.lang})
                self_with_lang = self.with_context(context_temp)

            else:
                raise ValidationError("No language in context and no language for the user set!")

        else:
            self_with_lang = self

        logger.info("Generating FSON email.template screenshots for lang %s and e-mail templates with ids: %s"
                    "" % (self_with_lang.env.context.get('lang', False), self_with_lang.ids))

        # GENERATE THE SCREENSHOT
        for r in self_with_lang:
            logger.info("Generate screenshot for email.template with id %s !" % r.id)

            if not r.fso_email_html_parsed:
                logger.error("E-Mail template (ID %s) field fso_email_html_parsed is empty! "
                             "Can not generate a screenshot!" % r.id)
                r.write({'screenshot': False, 'screenshot_pending': False})
                continue

            # Create a temp file to write the e-mail body html into
            now_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            email_body_file_name = 'emailtemplate_'+str(r.id)+'__'+now_str
            email_body_file = tempfile.NamedTemporaryFile(bufsize=0,
                                                          prefix=email_body_file_name,
                                                          suffix=".html",
                                                          delete=True)

            # Generate the screenshot and update the 'screenshot' field
            try:
                email_body_file.write(r.fso_email_html_parsed.encode(encoding='utf-8'))
                logger.info('Named Temporary File %s for screenshot generation was updated!' % email_body_file.name)
                screenshot_url = 'file://'+email_body_file.name
                screenshot_img = screenshot(screenshot_url,
                                            src_width=src_width, src_height=src_height,
                                            tgt_width=tgt_width, tgt_height=tgt_height)
                r.write({'screenshot': screenshot_img or False, 'screenshot_pending': False})
                logger.info("Screenshot for e-mail template (ID %s) for language %s successfully created"
                            "" % (r.id, r.env.context.get('lang', False)))

            # Unset the screenshot
            except Exception as e:
                logger.error("Could not create screenshot for e-mail template (ID %s):\n%s" % (r.id, repr(e)))
                r.write({'screenshot': False, 'screenshot_pending': False})

            # Make sure the temp file gets closed and deleted
            finally:
                logger.info('File %s for screenshot generation will be closed and deleted!' % email_body_file.name)
                email_body_file.close()

            if os.path.exists(email_body_file.name):
                logger.error('File %s for screenshot generation could not be deleted!' % email_body_file.name)

        return True

    # ------------
    # CRUD METHODS
    # ------------
    @api.model
    def create(self, vals):
        res = super(EmailTemplate, self).create(vals)
        res._update_fson_html_fields_and_screenshot_pending()
        return res

    @api.multi
    def write(self, vals):
        res = super(EmailTemplate, self).write(vals)
        if any(f in vals for f in ['fso_email_template', 'fso_template_view_id', 'body_html']):
            self._update_fson_html_fields_and_screenshot_pending()
        return res

    @api.multi
    def create_version(self, version_name=''):
        assert self.ensure_one(), _("E-Mail Template Versions can only be created for a single E-Mail Template")
        r = self
        version_name = version_name or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info("Create version of email.template with id %s" % r.id)
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

        # ATTENTION: DISABLED because non active records are not shown in version_ids therefore it appears empty
        # assert version_id in self.version_ids.ids, _("Version is not a Version of this E-Mail Template")

        r = self

        # Find the version
        version = self.sudo().browse([int(version_id)])
        assert version, _("Version to restore was not found!")
        assert version.version_of_email_id.id == r.id, _("Version is not a Version of this E-Mail Template")

        # Get data to restore
        data_to_restore = version.copy_data()[0]

        # Exclude fields that should not be restored
        # HINT: Sosync fields are added to the MAGIC_COLUMNS in fso_sosync so they will not be copied by default.
        #       Just as a safety measure they are excluded here also.
        data_to_restore = {key: value for (key, value) in data_to_restore.items() if key not in (
            'active', 'name', 'version_of_email_id', 'version_ids',
            'sosync_write_date', 'sosync_sync_date', 'sosync_fs_id')}

        # Create a new version from current data first
        logger.info("Create new version for email.template (ID %s) before restoring data from version with id %s"
                    "" % (r.id, version_id))
        assert r.create_version(), _("Could not create a version of the email template before restore!")

        # Update email template with data from version
        logger.info("Restore data from email.template version (ID %s) to email.template with id %s"
                    "" % (version_id, r.id))
        r.sudo().write(data_to_restore)

        return True

    @api.model
    def scheduled_screenshot_update(self):
        self.search([('screenshot_pending', '=', True)]).screenshot_update()
        return True
