# -*- coding: utf-8 -*-
from openerp import api, fields, models

import lxml.etree as et
import logging
logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    has_widget_manager = fields.Boolean(compute="_compute_has_widget_manager", string="Has Widget Manager")

    @api.multi
    @api.depends('website_url', 'seo_url')
    def _compute_has_widget_manager(self):
        for record in self:
            found = self.env['website.widget_manager'].search(
                ['|',
                   ('source_page', '=', record.website_url),
                   ('source_page', '=', record.seo_url)])
            if len(found) >= 1:
                record.has_widget_manager = True

    @api.multi
    def button_view_product_page(self):
        return {
            'name': 'View Product Page',
            'type': 'ir.actions.act_url',
            'res_model': 'ir.actions.act_url',
            'target': 'new',
            'url': self.website_url
        }

    @api.multi
    def button_open_widget_manager(self):
        self.ensure_one()
        active_product_template = self
        return {
            'name': 'View Widget Manager',
            'type': 'ir.actions.act_window',
            'res_model': 'website.widget_manager',
            'view_type': 'tree',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [
                '|',
                   ('source_page', '=', active_product_template.website_url),
                   ('source_page', '=', active_product_template.seo_url)
            ]
        }

    @api.multi
    def view_product_statistics(self):
        return {
            'name': 'View Product Statistics',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_type': 'graph',
            'view_mode': 'graph',
            'views': [(self.env.ref("website_sale_donate.sale_order_line_wsd_graph").id, 'graph')],
            'target': 'current',
            'domain': [
                '&',
                ('state', '!=', 'draft'),
                ('product_id', 'in', [variant.id for variant in self.product_variant_ids])
            ]
        }
