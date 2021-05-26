# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields


class ProductPublicCategoryStayOnPage(models.Model):
    _inherit = 'product.public.category'

    add_to_cart_stay_on_page = fields.Boolean(string='Add to Cart and stay on Page',
                                              help='Quick add buttons on product tiles will add the product to the '
                                                   'shopping cart but stay on the product listing page (instead of '
                                                   'jumping e.g. to the shopping cart or checkout page)')
