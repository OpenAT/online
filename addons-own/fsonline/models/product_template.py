# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp.tools.translate import _


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

    @api.multi
    @api.depends('website_url', 'seo_url')
    def _compute_widget_manager_ids(self):
        widget_manager_obj = self.env['website.widget_manager']

        for r in self:
            search_params = []
            if r.seo_url:
                search_params = ['|', ('source_page', '=like', '%' + r.seo_url)]
            search_params.append(('source_page', '=', r.website_url))
            widget_manager_rec = widget_manager_obj.search(search_params)
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
            'name': _('Product Page'),
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
            'name': _('Widget Manager'),
            'type': 'ir.actions.act_window',
            'res_model': 'website.widget_manager',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', active_product_template.widget_manager_ids.ids)],
            'context': {'default_source_page': active_product_template.website_url}
        }

    @api.multi
    def button_open_product_statistics(self):
        self.ensure_one()
        active_product_template = self
        product_ids = [variant.id for variant in active_product_template.product_variant_ids]
        return {
            'name': _('Product Statistics'),
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
