# -*- coding: utf-'8' "-*-"
import logging
import re
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.addons.fso_base.tools.validate import is_valid_hostname

logger = logging.getLogger(__name__)


class WebsiteDomainManager(models.Model):
    _name = 'website.website_domains'
    _description = 'Website Domain Manager'

    @api.model
    def get_domain_template_ids(self):
        # Get the ir.ui.view ids from the external_ids entries
        # HINT: The ir.model.data records are always active even if the related record is not
        x_ids = self.env['ir.model.data'].sudo().search(['&',
                                                         ('model', '=', 'ir.ui.view'),
                                                         ('name', '=like', '%website_domain_template%')
                                                         ])
        view_ids = [x.res_id for x in x_ids if x.res_id]
        return view_ids

    @api.model
    def _get_wdt_domain(self):
        domain = ['&',
                  ('id', 'in', self.get_domain_template_ids()),
                  '|', ('active', '=', False), ('active', '!=', False)
                  ]
        return domain

    @api.constrains('name')
    def _validate_name(self):
        if not is_valid_hostname(self.name):
            raise ValidationError(_("Field 'name' must be a valid hostname!\n"
                                    "E.g.: www.test-bob.at\n"
                                    "':' '&' '/' '?' '&' characters are not allowed!"))




    # TODO: check the domain (name) is a valid url
    name = fields.Char(string='Domain', required=True, translate=True, help='E.g.: spenden.test.at')
    port = fields.Char(string='Port', help='Domain Port')
    template = fields.Many2one(comodel_name='ir.ui.view', string="Domain Template", domain=_get_wdt_domain)
    redirect_url = fields.Char(string='Redirect URL', translate=True, help='E.g.: https://www.test.at/de/shop')

    _sql_constraints = [('domain_uniq', 'unique (domain)', 'The domain must be unique!')]
