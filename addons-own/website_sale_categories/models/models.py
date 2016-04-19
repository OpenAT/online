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

    cat_hide = fields.Boolean(string="Hide this Category from Cat-Navigation")
    cat_root = fields.Boolean(string="RootCateg. (Start Cat-Navigation from here)")
    one_page_checkout = fields.Boolean(string="One-Page-Checkout")
    # Topmost parent category:
    # Store the nearest parent category in the field cat_root_id  that has cat_root=True or, if no parent category has
    # cat_root set to True, set the topmost parent category for cat_root_id. Use the current category for cat_root_id if
    # no parent category is available or the current category has cat_root set to True.
    # HINT: This field is used in the category qweb-template to render the categories as well as for products shown at
    #       each category (domain filter in main.py)
    # ATTENTION: Hidden categories are treated like root categories even if root_cat is not set!
    cat_root_id = fields.Many2one(comodel_name='product.public.category',
                                  string='Nearest Root Category or UpMost Parent')
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
    redirect_url_after_form_feedback = fields.Char(string='Redirect URL after PP Form-Feedback',
                                                   help='Redirect to this URL after processing the Answer of the'
                                                        'Payment Provider instead of /shop/confirmation_static')

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

        # Update Cart and get the sales_order_line
        cu = super(sale_order, self)._cart_update(cr, uid, ids,
                                                  product_id=product_id,
                                                  line_id=line_id,
                                                  add_qty=add_qty,
                                                  set_qty=set_qty,
                                                  context=context, **kwargs)
        line_id = cu.get('line_id')
        sol_obj = self.pool.get('sale.order.line')
        sol = sol_obj.browse(cr, SUPERUSER_ID, line_id, context=context)

        # Update the sale_order_line with cat_root_id and cat_id if in kwargs
        # TODO: small_cart should also add cat_root_id - error reported by joe
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

        # Set the Sale Order cat_root_id field
        if sol.order_id:
            if sol_obj.search(cr, SUPERUSER_ID,
                              ['&',
                               ('order_id.id', '=', sol.order_id.id),
                               ('cat_root_id.id', '!=', sol.cat_root_id.id)], context=context):
                # Order-lines with different root-cat found, reset cat_root_id of the sales-order
                sol.order_id.cat_root_id = None
            else:
                # All order-lines have the same root-cat, set the cat_root_id of the sales-order
                sol.order_id.cat_root_id = sol.cat_root_id.id

        return cu
