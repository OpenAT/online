# -*- coding: utf-'8' "-*-"
import base64
import logging
import socket
import validators
import requests
from lxml import html
from urlparse import urlparse, urljoin, parse_qsl, urlunparse
from urllib import urlencode
from string import Template
from openerp import api, models, fields
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.http import request
from openerp.addons.base_tools.image import resize_to_thumbnail

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
# TODO: add PhantomJS and selenium to the ubuntu1404 saltstack formula
# TODO: Resize and crop the screenshot
# http://rachbelaid.com/capturing-screenshots-of-website-with-python/
# https://gist.github.com/tamaspap/f92a4725d56b2251a155f56b9612bf2e
# https://joecodeswell.wordpress.com/2015/08/25/headless-selenium-on-ubuntu-14-04-with-phantomjs-2-0/
def _get_screenshot(url, src_width=1024, src_height=768, tgt_width=int(), tgt_height=int()):
    # Import selenium
    try:
        from selenium import webdriver
    except ImportError:
        logger.error(_('Could not import selenium for screen-shot generation of %s!') % url)
        return False

    # Load PhantomJS()
    try:
        driver = webdriver.PhantomJS()
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
        #image = image_resize_image(image, size=(tgt_width, tgt_height), filetype='PNG')
        image = resize_to_thumbnail(image, box=(320, 240), fit='top')

    # Return Image
    return image


class website_aswidget_domains(models.Model):
    """URLs where as Widget is always True. Will redirect per Java Script if not loaded in an i-Frame"""
    _name = 'website.aswidget_domains'
    _description = 'Website as Widget (redirect) URLs'

    aswidget_domain = fields.Char(string='As Widget Domain', required=True, translate=True,
                                  help='E.g.: shop.test.com')
    redirect_url = fields.Char(string='Redirect URL', translate=True,
                               help='E.g.: https://www.test.com/fr/shop, '
                                    'Will only redirect by java script if window.self !== window.top')


class WebsiteAsWidget(models.Model):
    """
    Widget Manager with Widget-Embed-Code Generator
    """
    _name = 'website.aswidget'
    _description = 'AsWidget Manager'

    # TODO:
    # - Create Custom Widget for char fields (Source Path) called internal_url
    #   This widget will search for urls with the website.search_pages function just like the frontend

    # FIELD CONSTRAINS
    @api.constrains('source_path')
    def _validate_source_path(self):
        if self.source_path == '/':
            return
        if not self.source_path[0] == '/':
            raise ValidationError(_("Field source_path must be a relative path and therefore start with an '/'!"))
        # Check if the path can be found
        path = self.source_path.strip().rsplit("?")[0]
        pages = self.env['website'].search_pages(needle=path)
        if not any(path == page.get('loc') for page in pages):
            raise ValidationError(_("Field 'source_path' must be an existing relative page path!\n"
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
            self.target_screenshot = screenshot

    @api.onchange('source_path')
    def _onchange_source_path(self):
        if not self.source_path:
            return
        # Get current URL
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or request.httprequest.host_url
        url = urljoin(base_url, self.source_path)
        # Store screen-shot
        screenshot = _get_screenshot(url, tgt_width=320, tgt_height=240)
        if screenshot:
            self.source_screenshot = screenshot

    # COMPUTED FIELDS
    _iframe_prefix = 'fso_if'

    @api.depends('source_path', 'target_url')
    def _widget_code(self):
        for rec in self:
            # Only compute this fields if we have a source and a target for the iframe
            # HINT: Only Source but no target means that this page is only an aswidget landing page
            if not rec.source_path or not rec.target_url:
                return
            # Get the Base URL of the website
            # ATTENTION: We assume that the common customer address is used for web.base.url that points to our server!
            #            e.g.: http://spenden.care.at
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or request.httprequest.host_url

            # Add the aswidget parameter to the source path
            source_path = list(urlparse(rec.source_path))
            query = dict(parse_qsl(source_path[4]))
            query.update({'aswidget': 'True'})
            source_path[4] = urlencode(query)
            source_path = urlunparse(source_path)

            # Compose the source url for the iframe
            source_url = urljoin(base_url, source_path)

            # Generate the widget html code
            code_header = """<!-- Insert this 'script' element ONLY ONCE inside your html header -->
<script type="text/javascript" src="https://dadi.datadialog.net/website_tools/static/lib/iframe-resizer/js/iframeResizer.min.js" />
"""
            code = Template("""<!-- Insert this code in your html body where you want the widget to appear -->
<iframe id="$target_iframe_id" class="fso_iframe" src="$source_url" scrolling="no" frameborder="0" width="100%" style="width:100%; border:none; padding:0; margin:0;"></iframe>
<script type="text/javascript">iFrameResize({log: false, enablePublicMethods: true, checkOrigin: false, inPageLinks: true, heightCalculationMethod: taggedElement,}, '#$target_iframe_id')</script>
""")
            code = str(code.substitute(target_iframe_id=self._iframe_prefix + str(rec.id), source_url=source_url))

            # Store the widget code, iframe id and iframe url
            rec.widget_code_header = code_header
            rec.widget_code = code
            rec.source_url = source_url
            rec.iframe_id = self._iframe_prefix + str(rec.id)

    # ACTIONS
    @api.multi
    def action_check_widget(self):
        # TODO: Check if self is a recordset and if implement a for loop!
        if self.state == 'nocheck' or not self.source_url or not self.target_url:
            return
        errors = []

        # Check iframeResizer.min.js
        target_page = requests.get(self.target_url)
        target_tree = html.fromstring(target_page.text)
        # http://stackoverflow.com/questions/1390568/how-can-i-match-on-an-attribute-that-contains-a-certain-string
        script_iframeresizer = target_tree.xpath('//script[contains(@src, '
                                                 '"website_tools/static/lib/iframe-resizer/js'
                                                 '/iframeResizer")]')
        if len(script_iframeresizer) == 0:
            errors.append(_("iframeResizer.min.js script not found at %s") % self.target_url)
        elif len(script_iframeresizer) > 1:
            errors.append(_("iframeResizer.min.js script found multiple times at %s") % self.target_url)
        elif 'header' not in target_tree.getpath(script_iframeresizer[0]):
            errors.append(_("iframeResizer.min.js script found but not in html header %s"))

        # Error(s) found
        if errors:
            self.state = 'error'
            self.error = "".join(error+'\n' for error in errors)
            return

        # Check was successful
        self.state = 'ok'


    # FIELD DEFINITIONS
    active = fields.Boolean(string="active", default=True)
    notes = fields.Text(string="Notes", translate=True)
    error = fields.Text(string="Check Widget Errors", translate=True, readonly=True)
    # source
    source_path = fields.Char(string="Source Path", required=True)
    source_screenshot = fields.Binary(string="Source Screenshot")
    # target
    target_url = fields.Char(string="Target URL")
    target_screenshot = fields.Binary(string="Target Screenshot")
    # widget
    source_url = fields.Char(string='Source URL', compute='_widget_code', store=True, readonly=True)
    iframe_id = fields.Char(string='iframe html id', compute='_widget_code', store=True, readonly=True)
    widget_code = fields.Text(string='HTML-Body Embed Code', compute='_widget_code', store=True, readonly=True)
    widget_code_header = fields.Text(string='HTML-Header Embed Code', compute='_widget_code', store=True, readonly=True)
    # state
    state = fields.Selection([
            ('new', "New"),
            ('ok', "OK"),
            ('nocheck', "No Check"),
            ('error', "Error"),
        ], default='new')
