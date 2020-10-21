# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from openerp.addons.website_sale_donate.controllers.main import website_sale_donate

import logging
logger = logging.getLogger(__name__)


class WebsiteSaleDonateGTM(website_sale_donate):

    def order_lines_2_gtm(self, order_lines):
        """ Transform sale order lines to google tag manager dict """
        products = []
        for line in order_lines:
            if line.product_id:
                products.append({
                    'id': line.product_tmpl_id.id,
                    'name': line.product_id.name,
                    'price': line.price_unit,
                    # 'brand': 'Google',
                    'category': line.cat_id.id if line.cat_id else 'False',
                    'variant': line.product_id.id,
                    'quantity': line.product_uos_qty,
                    # 'coupon': ''
                    # Not google Tag Manager conform use dimension[n] and metric[n] instead
                    'price_donate': line.price_donate or 'False',

                    # Custom Dimensions
                    # -----------------
                    # This is needed since the Tag Manager does not accept custom fields

                    # 'fs_product_type': line.product_id.fs_product_type or 'False',
                    # 'html_template': line.product_id.product_page_template or 'False',
                    # 'css_theme': line.product_id.website_theme or 'False',
                    # 'payment_interval_id': line.payment_interval_id.id if line.payment_interval_id else 'False',
                    # 'payment_interval_name': line.payment_interval_name or 'False',
                    # 'payment_interval_xmlid': line.payment_interval_xmlid or 'False',

                    'dimension1': line.product_id.fs_product_type or 'False',
                    'dimension2': line.product_id.product_page_template or 'False',
                    'dimension3': line.product_id.website_theme or 'False',
                    'dimension4': line.payment_interval_id.id if line.payment_interval_id else 'False',
                    'dimension5': line.payment_interval_name or 'False',
                    'dimension6': line.payment_interval_xmlid or 'False',
                })
        return products

    def order_2_gtm(self, order):
        """ Prepare the sale order data for google tag manager """
        return {
            'currencyCode': order.currency_id.name,
            'order_data': {
                'id': str(order.id)+'__'+order.name,
                'affiliation': 'Fundraising Studio Online',
                'revenue': order.amount_total,
                'tax': order.amount_tax,
                # 'shipping': '5.99',
                # 'coupon': 'SUMMER_SALE'
            },
            'products': self.order_lines_2_gtm(order.order_line)
        }

    @http.route(['/shop/sale_order_data_for_gtm'], type='json', auth="public")
    def sale_order_data_for_gtm(self, **post):
        """ return data about the last sale order as JSON prepared for google tag manager"""
        gtm_data = {}
        sale_order_id = request.session.get('sale_order_id')
        logger.info('sale_order_id: %s' % sale_order_id)
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            gtm_data = self.order_2_gtm(order)
            logger.info('gtm_data %s' % gtm_data)
        return gtm_data
