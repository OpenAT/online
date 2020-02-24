# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields

__author__ = 'Michael Karrer'


# Product Template
# ATTENTION: There are unported parts for product.template in website_sale_donate.py !
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

    @api.onchange('fs_product_type')
    def _onchange_set_fs_workflow_by_fs_product_type(self):
        if self.fs_product_type in ['donation', 'godparenthood', 'sponsorship', 'membership']:
            self.fs_workflow = 'donation'
        else:
            self.fs_workflow = 'product'

    @api.multi
    def write(self, vals):
        if vals and 'fs_product_type' in vals and not 'fs_workflow' in vals:
            if vals.get('fs_product_type') in ['donation', 'godparenthood', 'sponsorship', 'membership']:
                vals['fs_workflow'] = 'donation'
            else:
                vals['fs_workflow'] = 'product'
        return super(ProductTemplate, self).write(vals)
