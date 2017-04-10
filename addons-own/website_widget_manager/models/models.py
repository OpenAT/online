# -*- coding: utf-'8' "-*-"
import base64
import logging
import socket
import validators
import requests
import os
from furl import furl
from lxml import html
from urlparse import urlparse, urljoin, parse_qsl, urlunparse
from string import Template
from openerp import api, models, fields
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.image import resize_to_thumbnail

logger = logging.getLogger(__name__)


def _check_url(url):
    assert isinstance(url, (str, unicode)), _("URL must be a string!")

    # Check for a valid URL
    if not validators.url(url):
        message = _('The URL is not valid! \nURL: %s\n\n'
                    'Please provide valid URL!\nE.g.: https://www.google.at/search?q=datadialog') % url
        warning = {'warning': {'title': _('Warning'), 'message': message}}
        return False, warning

    # Make a quick DNS check instead of a full HTTP GET request (because a request.get() can be really slow)
    try:
        socket.gethostbyname(urlparse(url).hostname)
    except Exception:
        message = _('DNS check failed for url %s!') % url
        warning = {'warning': {'title': _('Warning'), 'message': message}}
        return False, warning

    return True, {}


# Get a screen-shot for the target URL
# http://randomdotnext.com/selenium-phantomjs-on-aws-ec2-ubuntu-instance-headless-browser-automation/
# TODO: Add Timeouts
def _get_screenshot(url, src_width=1024, src_height=768, tgt_width=int(), tgt_height=int()):
    # Import selenium
    try:
        from selenium import webdriver
    except ImportError:
        logger.error(_('Could not import selenium for screen-shot generation of %s!') % url)
        return False

    # Load PhantomJS()
    try:
        driver = webdriver.PhantomJS(service_log_path=os.path.devnull)
    except Exception as error:
        logger.error(_('Could not load PhantomJS() for screen-shot generation of %s!\n\n%s\n') % (url, error))
        return False

    # Generate screen-shot
    try:
        driver.set_window_size(src_width, src_height)
        driver.get(url)
        image = driver.get_screenshot_as_png()
        image = base64.b64encode(image)
    except Exception as error:
        logger.warning('Could not generate screen-shot for url:\n\n%s\n' % error)
        return False

    # Resize Image
    if tgt_width or tgt_height:
        x = tgt_width or 320
        y = tgt_height or 240
        image = resize_to_thumbnail(image, box=(x, y), fit='top')

    # Return Image
    return image


class WebsiteAsWidget(models.Model):
    """
    Widget Manager with Widget-Embed-Code Generator
    """
    _name = 'website.widget_manager'
    _description = 'Widget Manager'
    _rec_name = 'source_url'
    _order = 'sequence'

    # TODO:
    # - Create Custom Widget for char fields (Source Path) called internal_url
    #   This widget will search for urls with the website.search_pages function just like the frontend

    # FIELD CONSTRAINS
    @api.constrains('source_page')
    def _validate_source_page(self):
        if self.source_page == '/':
            return
        if not self.source_page[0] == '/':
            raise ValidationError(_("Field source_page must be a relative path and therefore start with an '/'!"))
        # Check if the path can be found
        path = self.source_page.strip().rsplit("?")[0]
        pages = self.env['website'].search_pages(needle=path)
        if not any(path == page.get('loc') for page in pages):
            raise ValidationError(_("Field 'source_page' must be an existing relative page path!\n"
                                    "E.g.: /shop?category=12\n\n"
                                    "Pages found:\n%s\n") % pages)

    @api.constrains('target_url')
    def _validate_target_url(self):
        if self.target_url:
            if not validators.url(self.target_url):
                raise ValidationError(_("Field 'target_url' must be a valid URL!\n"
                                        "E.g.:\n"
                                        "https://www.google.at\nor\n"
                                        "https://www.google.at/search?q=datadialog&*&rct=j\n"))
    # ONCHANGE UI CHANGES
    @api.onchange('target_url')
    def _onchange_target_url(self):
        if not self.target_url:
            return
        # Check URL
        url_check, warning = _check_url(self.target_url)
        if warning:
            return warning
        # Store screen-shot
        screenshot = _get_screenshot(self.target_url, tgt_width=320, tgt_height=240)
        if screenshot:
            # return {'target_screenshot': screenshot}
            self.target_screenshot = screenshot

    @api.onchange('source_page')
    def _onchange_source_page(self):
        if self.source_protocol and self.source_domain and self.source_page:
            # HINT: rec.source_protocol, rec.source_domain and rec.source_page are mandatory fields
            # ATTENTION: To avoid recursion store result from furl in variable first
            source_base = furl().set(scheme=self.source_protocol,
                                     host=self.source_domain.name,
                                     port=self.source_domain.port)
            source_url = source_base.join(self.source_page)
            source_url.args['noiframeredirect'] = 'True'
            source_url = source_url.url
            # Store screen-shot
            screenshot = _get_screenshot(source_url, tgt_width=320, tgt_height=240)
            if screenshot:
                # return {'source_screenshot': screenshot}
                self.source_screenshot = screenshot

    # CONSTANTS
    _iframe_prefix = 'fso_if'
    _script_path = "/website_widget_manager/static/lib/iframe-resizer/js/iframeResizer.min.js"

    # COMPUTED FIELDS
    @api.depends('source_protocol', 'source_domain', 'source_page', 'target_url')
    def _widget_code(self):
        for rec in self:
            if not rec.source_protocol or not rec.source_domain or not rec.source_page:
                continue

            # Compose the source url
            # HINT: rec.source_protocol, rec.source_domain and rec.source_page are mandatory fields
            # ATTENTION: To avoid recursion store result from furl in variable first
            source_base = furl().set(scheme=rec.source_protocol,
                                     host=rec.source_domain.name,
                                     port=rec.source_domain.port)
            source_url = source_base.join(rec.source_page).url

            # Return if no target url was set
            # HINT: No target url means that this page is a landing page (maybe with different website domain template)
            if not rec.target_url:
                rec.source_url = source_url
                continue

            # Store the iframe id before we continue
            rec.iframe_id = rec._iframe_prefix + str(rec.id)

            # Generate the head embed code
            script_url = source_base.join(rec._script_path).url
            widget_code_header = Template("""<!-- Insert this 'script' element ONLY ONCE inside your html header -->
<script type="text/javascript" src="$script_url" />
""").substitute(script_url=script_url)

            # Generate the widget embed code
            widget_code = Template("""<!-- Insert this code in your html body where you want the widget to appear -->
<iframe id="$target_iframe_id" class="fso_iframe" src="$source_url" scrolling="no" frameborder="0" width="100%" style="width:100%; border:none; padding:0; margin:0;"></iframe>
<script type="text/javascript">iFrameResize({log: false, enablePublicMethods: true, checkOrigin: false, inPageLinks: true, heightCalculationMethod: taggedElement,}, '#$target_iframe_id')</script>
""").substitute(target_iframe_id=rec.iframe_id, source_url=source_url)

            # HINT: To avoid recursion (because of the iframe_id) we use single writes here instead of .write({})
            rec.source_url = source_url
            rec.widget_code_header = widget_code_header
            rec.widget_code = widget_code

    # ACTIONS
    @api.multi
    def action_check_widget(self):
        for record in self:
            if record.state == 'nocheck' or not record.source_url or not record.target_url:
                continue
            errors = []
            warnings = []

            # Check if FS-Online page exits
            try:
                record._validate_source_page()
            except ValidationError:
                errors.append(_('Source page can not be found!'))

            # Get target page
            target_page = requests.get(record.target_url)
            target_tree = html.fromstring(target_page.text)

            # Check iframeResizer.min.js
            # http://stackoverflow.com/questions/1390568/how-can-i-match-on-an-attribute-that-contains-a-certain-string
            script_iframeresizer = target_tree.xpath('//script[contains(@src, '
                                                     '"website_widget_manager/static/lib/iframe-resizer/js'
                                                     '/iframeResizer")]')
            if len(script_iframeresizer) == 0:
                errors.append(_("iframeResizer script not found at %s") % record.target_url)
            elif len(script_iframeresizer) > 1:
                warnings.append(_("iframeResizer script found multiple times at %s") % record.target_url)
            elif 'head' not in target_tree.getpath(script_iframeresizer[0]):
                warnings.append(_("iframeResizer script found but not in html head tag %s"))

            # Update record
            record.write({
                'state': 'error' if errors else 'warning' if warnings else 'ok',
                'check_log': "".join(msg+'\n\n' for msg in (errors + warnings)),
            })

    @api.multi
    def action_toggle_do_not_check(self):
        for rec in self:
            rec.check_log = ''
            rec.state = 'nocheck' if rec.state != 'nocheck' else 'new'


    # FIELD DEFINITIONS
    active = fields.Boolean(string="active", default=True)
    sequence = fields.Integer(string='Order')
    notes = fields.Text(string="Notes", translate=True)
    check_log = fields.Text(string="Check Log", translate=True, readonly=True)
    # source
    source_protocol = fields.Selection([('http', "http://"),
                                        ('https', "https://")],
                                       string="Protocol", default='https', required=True)
    source_domain = fields.Many2one(string='Source Domain', comodel_name='website.website_domains', required=True)
    source_page = fields.Char(string="Source Page", required=True)
    source_screenshot = fields.Binary(string="Source Screenshot")
    # target
    target_url = fields.Char(string="Target Page")
    target_screenshot = fields.Binary(string="Target Screenshot")
    # widget parameters
    source_url = fields.Char(string='Source URL',
                             compute='_widget_code', compute_sudo=True, store=True, readonly=True)
    iframe_id = fields.Char(string='iframe html id',
                            compute='_widget_code', compute_sudo=True, store=True, readonly=True)
    widget_code = fields.Text(string='HTML-Body Embed Code',
                              compute='_widget_code', compute_sudo=True, store=True, readonly=True)
    widget_code_header = fields.Text(string='HTML-Header Embed Code',
                                     compute='_widget_code', compute_sudo=True, store=True, readonly=True)
    # state
    state = fields.Selection([
            ('new', "New"),
            ('ok', "OK"),
            ('nocheck', "No Check"),
            ('warning', "Warning"),
            ('error', "Error"),
        ], default='new')
