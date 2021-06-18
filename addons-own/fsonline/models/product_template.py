# -*- coding: utf-8 -*-
from openerp import api, fields, models

import lxml.etree as et
import logging
logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    has_widget_manager = fields.Boolean(compute="_compute_has_widget_manager", string="Has Widget Manager")

    @api.multi
    @api.depends('website_url')
    def _compute_has_widget_manager(self):
        for record in self:
            widget_manager_obj = self.env['website.widget_manager'].search([('source_page', '=', record.website_url)])
            if widget_manager_obj and widget_manager_obj.id:
                record.has_widget_manager = True

    @api.multi
    def view_product_page(self):
        return {
            'name': 'View Product Page',
            'type': 'ir.actions.act_url',
            'res_model': 'ir.actions.act_url',
            'target': 'new',
            'url': self.website_url
        }

    @api.multi
    def view_widget_manager(self):
        widget_manager_obj = self.env['website.widget_manager'].search([('source_page', '=', self.website_url)])
        if widget_manager_obj and widget_manager_obj.id:
            return {
                'name': 'View Widget Manager',
                'type': 'ir.actions.act_window',
                'res_model': 'website.widget_manager',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'res_id': widget_manager_obj.id
            }
        return False

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
