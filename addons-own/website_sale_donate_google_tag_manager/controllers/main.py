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
                    'id': line.product_id.id,
                    'name': line.product_id.name,
                    'price': line.price_unit,
                    'category': line.cat_id.id if line.cat_id else 'False',
                    'quantity': line.product_uos_qty,
                })
        return products

    def order_2_gtm(self, order):
        """ Prepare the sale order data for google tag manager """
        return {
            'currencyCode': order.currency_id.name,
            'order_data': {
                'id': str(order.id)+'__'+order.name,
                'affiliation': order.company_id.name,
                'revenue': order.amount_total,
                'tax': order.amount_tax,
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
