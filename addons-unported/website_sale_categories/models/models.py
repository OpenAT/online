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

from openerp import tools
from openerp import api, models, fields
from openerp import SUPERUSER_ID


# Extend the Product Public Category model with two new fields:
# desc = Category Description displayed in product list views
# productinfo = Additional information displayed on product pages for this category
class product_public_category_menu(models.Model):
    _inherit = 'product.public.category'

    cat_desc_showatchilds = fields.Html(string="Top-Description shown at Child Categories")
    cat_desc = fields.Html(string="Top-Category-Description")

    cat_descbottom_showatchilds = fields.Html(string="Bottom-Description shown at Child Categories")
    cat_descbottom = fields.Html(string="Bottom-Category-Description")

    cat_hide = fields.Boolean(string="Hide in Menu")
    cat_root = fields.Boolean(string="Is Root Category")
    one_page_checkout = fields.Boolean(string="One-Page-Checkout")
    # Topmost parent category:
    # Store the nearest parent category in the field cat_root_id  that has cat_root=True or, if no parent category has
    # cat_root set to True, set the topmost parent category for cat_root_id. Use the current category for cat_root_id if
    # no parent category is available or the current category has cat_root set to True.
    # HINT: This field is used in the category qweb-template to render the categories as well as for products shown at
    #       each category (domain filter in main.py)
    # ATTENTION: Hidden categories are treated like root categories even if root_cat is not set!
    cat_root_id = fields.Many2one(comodel_name='product.public.category',
                                  string='Parent Root Category')
    # DIV boxes classes
    cat_products_grid_before = fields.Char(string="CSS classes for div#products_grid_before")
    cat_products_grid = fields.Char(string="CSS classes for div#products_grid")
    # Number of Grid-Items
    cat_products_grid_ppg = fields.Integer(string="Products per Page")
    cat_products_grid_ppr = fields.Integer(string="Products per Row")
    # Grid Template selector
    # HINT: Right now this is only used to select between the original grid and the original list layout
    #       this is needed because the original xpath option would always set it for the complete shop
    grid_template = fields.Selection([('website_sale.products', 'Default Grid Layout'),
                                      ('website_sale_categories.products_listing', 'List Layout')],
                                     string="Shop Grid Template")
    # Redirect Url after form feedback of the payment provider
    redirect_url_after_form_feedback = fields.Char(string='Redirect URL after Payment',
                                                   help='Redirect to this URL after processing the Answer of the'
                                                        'Payment Provider instead of /shop/confirmation_static',
                                                   translate=True)
    # Sales Team for Sales Orders
    cat_section_id = fields.Many2one(comodel_name='crm.case.section', string='Sales Team')


    # Update the field cat_root_id at addon installation or update
    def init(self, cr, context=None):
        print "INIT OF website_sale_categories"
        allcats = self.search(cr, SUPERUSER_ID, [])
        for catid in allcats:
            cat = self.browse(cr, SUPERUSER_ID, catid)
            # To set the parent_id will trigger the recalculation of cat_root_id in the write method
            cat.write({"parent_id": cat.parent_id.id or None})

    @api.onchange('cat_hide')
    def set_cat_root(self):
        if self.cat_hide:
            self.cat_root = True

    # Set cat_root_id
    def create(self, cr, uid, vals, context=None):
        cat_id = super(product_public_category_menu, self).create(cr, uid, vals, context=context)

        category = self.browse(cr, SUPERUSER_ID, cat_id)

        # Call Write again after creation to update the root cat
        category.write(vals)

        return cat_id

    # Recalculate the cat_root_id
    @api.multi
    def write(self, vals):
        if self.ensure_one():

            # ATTENTION: Hidden categories are treated like root categories!
            if vals.get('cat_hide') or vals.get('cat_root'):
                vals['cat_root'] = True

            # cat_hide or cat_root was set
            if vals.get('cat_root'):
                vals['cat_root_id'] = self.id
            # cat_hide or cat_root was NOT set = Check Parents
            else:
                # Search for cat_root in parent if any parent found
                # HINT: parent_id in vals could also be "False"! (or no self.parent_id)
                parent = self.browse(vals['parent_id']) if 'parent_id' in vals else self.parent_id
                if parent:
                    while True:
                        if parent.cat_root or parent.cat_hide or not parent.parent_id:
                            vals['cat_root_id'] = parent.id
                            break
                        else:
                            parent = parent.parent_id
                else:
                    vals['cat_root_id'] = self.id


            # Update self
            res = super(product_public_category_menu, self).write(vals)

            # Re-Calculate the cat_root_id of the child categories (if any)
            categories = self.env['product.public.category'].search(['&',
                                                                     ('id', 'child_of', int(self.id)),
                                                                     ('id', 'not in', self.ids)])
            for child_cat in categories:
                cat = child_cat
                while True:
                    if cat.cat_root or cat.cat_hide or not cat.parent_id:
                        if cat.ids:
                            child_cat.cat_root_id = cat.id
                        break
                    else:
                        cat = cat.parent_id

            # Return
            return res
        else:
            raise Exception('Please change public categories one by one!')

    @api.multi
    def unlink(self):

        child_categories = self.env['product.public.category']
        # Find and store all Child Categories
        for category in self:
            # Find existing Child Categories
            child_categories += category.env['product.public.category'].search(['&',
                                                                     ('id', 'child_of', int(category.id)),
                                                                     ('id', 'not in', category.ids)])

        # Unlink the categories (so they do not disturb the recalculation for child cats)
        res = super(product_public_category_menu, self).unlink()

        # Recalculate the RootCats for any found child categories
        for child_cat in child_categories:
            child_cat.write({"parent_id": child_cat.parent_id.id or None})

        return res

# Add fields for public RootCat and Public Cat to the sales_order_line
class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    cat_root_id = fields.Many2one(comodel_name='product.public.category', string='RootCateg.')
    cat_id = fields.Many2one(comodel_name='product.public.category', string='Categ.')


# Store the cat_id and cat_root_id in the sale order line and in the sale order if all lines are similar!
class sale_order(models.Model):
    _inherit = "sale.order"

    cat_root_id = fields.Many2one(comodel_name='product.public.category', string='RootCateg.',)

    def _cart_update(self, cr, uid, ids, product_id=None, line_id=None, add_qty=0, set_qty=0, context=None, **kwargs):

        # Get sale order and sale order line
        so = None
        sol_obj = self.pool.get('sale.order.line')
        if line_id:
            sol = sol_obj.browse(cr, SUPERUSER_ID, line_id, context=context)
            try:
                so = sol.order_id
            except:
                pass

        # Update sale order and sale order line (= product cart)
        cu = super(sale_order, self)._cart_update(cr, uid, ids,
                                                  product_id=product_id,
                                                  line_id=line_id,
                                                  add_qty=add_qty,
                                                  set_qty=set_qty,
                                                  context=context, **kwargs)

        # In case the order line just got created update the sol and so
        if isinstance(cu, dict) and cu.get('quantity', 0) > 0 and cu.get('line_id'):
            line_id = cu.get('line_id')
            sol = sol_obj.browse(cr, SUPERUSER_ID, line_id, context=context)
            try:
                if sol.order_id:
                    so = sol.order_id
            except:
                pass

            # Update the sale_order_line with cat_root_id and cat_id
            try:
                cat_root_id = int(kwargs.get('cat_root_id'))
                sol.cat_root_id = cat_root_id
            except:
                pass
            try:
                cat_id = int(kwargs.get('cat_id'))
                sol.cat_id = cat_id
            except:
                pass

        # Set the cat_root_id for Sale Order and for sale_order-deliver_lines
        try:
            if so and so.order_line:
                # Get all cat_root_ids for non deliver so lines (or False if not cat_root exists)
                cr_ids = [x.cat_root_id.id if x.cat_root_id else False for x in so.order_line if not x.is_delivery]
                # Check if all cat_root_ids are the same
                if cr_ids and False not in cr_ids and all(x == cr_ids[0] for x in cr_ids):
                    # All order-lines have the same root-cat, set the cat_root_id of the sales-order
                    so.cat_root_id = cr_ids[0]
                    # Set the Sales Team if set in root cat
                    if so.cat_root_id.cat_section_id:
                        so.section_id = so.cat_root_id.cat_section_id.id
                        # Set the Team Leader of the Sales Team as the Sales-Man of the SO
                        # HINT: This is not relevant for the followers of the SO only the followers of the sales team
                        #       will be added to the follower list of the SO
                        if so.cat_root_id.cat_section_id.user_id:
                            so.user_id = so.cat_root_id.cat_section_id.user_id.id
                    # Set the root cat also for the delivery line if any
                    for line in [x for x in so.order_line if x.is_delivery]:
                        line.cat_root_id = cr_ids[0]
                else:
                    # Reset sale order cat_root_id
                    so.cat_root_id = None
                    # Reset Delivery lines if any
                    for line in [x for x in so.order_line if x.is_delivery]:
                        line.cat_root_id = None
        except:
            pass

        return cu
