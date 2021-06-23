# -*- coding: utf-8 -*-
from openerp import api, fields, models

import lxml.etree as et
import logging
logger = logging.getLogger(__name__)


class ProductTemplateExtensions(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    widget_manager_ids = fields.One2many(string='Widget Managers',
                                         comodel_name='website.widget_manager',
                                         compute="_compute_widget_manager_ids",
                                         readonly=True,
                                         translate=True)

    widget_manager_count = fields.Integer(string='Widget Manager Count',
                                          compute="_compute_widget_manager_count",
                                          readonly=True,
                                          translate=True)

    seo_relative_url = fields.Char(string="SEO Relative URL",
                                   compute="_compute_seo_relative_url",
                                   readonly=True,
                                   translate=True)

    @api.multi
    @api.depends('seo_url')
    def _compute_seo_relative_url(self):
        for r in self:
            r.seo_relative_url = '/shop/product/%s' % r.seo_url

    @api.multi
    @api.depends('website_url', 'seo_url')
    def _compute_widget_manager_ids(self):
        widget_manager_obj = self.env['website.widget_manager']
        for r in self:
            widget_manager_rec = widget_manager_obj.search([
                '|',
                    ('source_page', '=', r.website_url),
                    ('source_page', '=', r.seo_relative_url)
            ])
            r.widget_manager_ids = widget_manager_rec

    @api.multi
    @api.depends('website_url', 'seo_url')
    def _compute_widget_manager_count(self):
        for r in self:
            r.widget_manager_count = len(r.widget_manager_ids) or 0

    @api.multi
    def button_open_product_page(self):
        self.ensure_one()
        active_product_template = self
        return {
            'name': 'Product Page',
            'type': 'ir.actions.act_url',
            'res_model': 'ir.actions.act_url',
            'target': 'new',
            'url': active_product_template.website_url
        }

    @api.multi
    def button_open_widget_manager(self):
        self.ensure_one()
        active_product_template = self
        return {
            'name': 'Widget Manager',
            'type': 'ir.actions.act_window',
            'res_model': 'website.widget_manager',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [
                '|',
                   ('source_page', '=', active_product_template.website_url),
                   ('source_page', '=', active_product_template.seo_relative_url)
            ]
        }

    @api.multi
    def button_open_product_statistics(self):
        self.ensure_one()
        active_product_template = self
        product_ids = [variant.id for variant in active_product_template.product_variant_ids]
        return {
            'name': 'Product Statistics',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_type': 'form',
            'view_mode': 'graph,tree,form',
            'views': [(self.env.ref("website_sale_donate.sale_order_line_wsd_graph").id, 'graph')],
            'target': 'current',
            'context': {
                'search_default_filter_confirmed': 1,
                'search_default_product_id': product_ids
            }
        }
