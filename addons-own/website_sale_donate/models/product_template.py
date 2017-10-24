# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields

__author__ = 'Michael Karrer'


# Product Template
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    website_published_start = fields.Datetime('Website Published Start')
    website_published_end = fields.Datetime('Website Published End')
    website_visible = fields.Boolean('Visible in Website (computed)', readonly=True,
                                     compute="compute_website_visible", store=True)

    @api.depends('active', 'website_published', 'website_published_start', 'website_published_end')
    def compute_website_visible(self):
        for pt in self:
            now = fields.Datetime.now()
            if pt.active and pt.website_published and (
                        (not pt.website_published_start or pt.website_published_start <= now)
                    and (not pt.website_published_end or pt.website_published_end > now)):
                pt.website_visible = True
            else:
                pt.website_visible = False
