# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from openerp.addons.website_sale_donate.controllers.main import website_sale_donate
from openerp.tools.float_utils import float_repr

import logging
logger = logging.getLogger(__name__)


class WebsiteSaleDonateGTM(website_sale_donate):

    def order_lines_2_gtm(self, order_lines):
        """ Transform sale order lines to google tag manager dict """
        products = []
        for line in order_lines:
            if line.product_id:
                products.append({
                    # 'id': line.product_tmpl_id.id,
                    'name': line.product_id.name,
                    'price': float_repr(line.price_unit, 2),
                    # 'brand': 'Google',
                    'category': str(line.cat_id.id) if line.cat_id else 'no-category',
                    'variant': str(line.product_id.id),
                    'quantity': str(line.product_uos_qty),
                    # 'coupon': ''

                    # Custom Dimensions
                    # -----------------
                    # This is needed since the Tag Manager does not accept custom fields
                    'dimension1': line.product_id.fs_product_type or 'no-frst-product-type',
                    'dimension2': line.product_id.product_page_template or 'no-product-page-template',
                    'dimension3': line.product_id.website_theme or 'no-product-website-theme',
                    'dimension4': str(line.payment_interval_id.id) if line.payment_interval_id else 'no-payment-interval-id',
                    'dimension5': line.payment_interval_name or 'no-payment-interval-name',
                    'dimension6': line.payment_interval_xmlid or 'no-payment-interval-xmlid',
                })
        return products

    def order_2_gtm(self, order):
        """ Prepare the sale order data for google tag manager """
        return {
            'currencyCode': order.currency_id.name,
            'order_data': {
                'id': str(order.id)+'__'+order.name,
                'affiliation': 'Fundraising Studio Online',
                'revenue': float_repr(order.amount_total, 2),
                'tax': float_repr(order.amount_tax, 2),
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
        logger.info('sale_order_data_for_gtm: sale_order_id: %s' % sale_order_id)
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            gtm_data = self.order_2_gtm(order)
            logger.info('gtm_data %s' % gtm_data)
        return gtm_data

    # @http.route(['/shop/product_name_for_gtm'], type='json', auth="public")
    # def product_name_for_gtm(self, product_product_id, **post):
    #     product = request.env['product.product'].sudo().search([('id', '=', product_product_id)])
    #     return product.name
