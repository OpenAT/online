# -*- coding: utf-'8' "-*-"
import logging
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.addons.fso_base.tools.validate import is_valid_hostname

logger = logging.getLogger(__name__)


class WebsiteDomainTemplates(models.Model):
    _name = "website.domain_templates"

    name = fields.Char(string="Domain Template Name", required=True)
    frontend_css = fields.Text(string="Frontend Assets CSS",
                               help="Add style tags with css. "
                                    "Style tag content Will be merged into frontend_assets css.")
    after_header = fields.Html(string="After Header")
    after_footer = fields.Html(string="After Footer")


class WebsiteDomainManager(models.Model):
    _name = 'website.website_domains'
    _description = 'Website Domain Manager'

    @api.constrains('name')
    def _validate_name(self):
        if not is_valid_hostname(self.name):
            raise ValidationError(_("Field 'name' must be a valid hostname!\n"
                                    "E.g.: www.test-bob.at\n"
                                    "':' '&' '/' '?' '&' characters are not allowed!"))

    name = fields.Char(string='Domain', required=True, help='E.g.: spenden.test.at')
    port = fields.Char(string='Port', help='Domain Port')
    # template = fields.Many2one(comodel_name='ir.ui.view', string="Domain Template", domain=_get_wdt_domain)
    domain_template_id = fields.Many2one(comodel_name='website.domain_templates', string="Domain Template")
    redirect_url = fields.Char(string='Redirect URL', help='E.g.: https://www.test.at/de/shop')

    _sql_constraints = [('domain_uniq', 'unique (name)', 'The domain must be unique!')]
