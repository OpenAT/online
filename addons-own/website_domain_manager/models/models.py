# -*- coding: utf-'8' "-*-"
import logging
from openerp import api, models, fields

logger = logging.getLogger(__name__)


class WebsiteDomainManager(models.Model):
    _name = 'website.website_domains'
    _description = 'Website Domain Manager'

    @api.model
    def _get_wdt_domain(self):
        x_ids = self.env['ir.model.data'].sudo().search(['&',
                                                         ('model', '=', 'ir.ui.view'),
                                                         ('name', '=like', '%website_domain_template%')
                                                         ])
        view_ids = [x.res_id for x in x_ids if x.res_id]
        domain = ['&',
                  ('id', 'in', view_ids),
                  '|', ('active', '=', False), ('active', '!=', False)
                  ]
        return domain

    # TODO: check the domain (name) is a valid url
    name = fields.Char(string='Domain', required=True, translate=True, help='E.g.: spenden.test.at')
    template = fields.Many2one(comodel_name='ir.ui.view', string="Domain Template", domain=_get_wdt_domain
                               )
    redirect_url = fields.Char(string='Redirect URL', translate=True, help='E.g.: https://www.test.at/de/shop')

    _sql_constraints = [('domain_uniq', 'unique (domain)', 'The domain must be unique!')]
