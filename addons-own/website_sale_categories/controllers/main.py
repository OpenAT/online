# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request

from openerp.addons.website_sale.controllers import main

# import the base controller class to inherit from
from openerp.addons.website_sale.controllers.main import website_sale


class website_sale_categories(website_sale):

    def _find_attr_in_cat_tree(self, category, attribute=str()):
        # Search up the category tree to the next root cat or to the top
        # Return the attribute value or false
        cat = category
        while True:
            if cat[attribute]:
                return cat[attribute]
            # If we have a parent id AND we are not a root cat: continue search
            elif cat.parent_id and cat.cat_root_id.id != cat.id:
                cat = cat.parent_id
                continue
            else:
                return False

    @http.route()
    def shop(self, page=0, category=None, search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        # Set the Default Grid in case no category was found or nothing set in any cat for PPG and PPR
        main.PPG = 20
        main.PPR = 4

        # Set products grid raster and templates
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            # Search up the category tree
            ppg = self._find_attr_in_cat_tree(category, attribute='cat_products_grid_ppg')
            if ppg:
                main.PPG = ppg
            ppr = self._find_attr_in_cat_tree(category, attribute='cat_products_grid_ppr')
            if ppr:
                main.PPR = ppr

        page = super(website_sale_categories, self).shop(page=page, category=category, search=search, **post)

        if category:
            # Set Template for the shop grid (or list view)
            # Shop Grid Qweb Template based on the grid_template field
            # HINT: qcontext holds the initial values the qweb template was called with
            # HINT: The first attribute of website.render is the template ID
            template = self._find_attr_in_cat_tree(category, attribute='grid_template')
            if template:
                page = request.website.render(template, page.qcontext)

        return page

    # List only products in the same cat_root_id tree:
    def _get_search_domain(self, search, category, attrib_values):
        domain = super(website_sale_categories, self)._get_search_domain(search, category, attrib_values)
        category_obj = request.registry['product.public.category']
        if category:
            # 1.) Find all relevant categories (self, and children with the same cat_root_id)
            #     HINT: child_of operator will find self and children! (so not only children as maybe expected)
            child_categories = category_obj.search(request.cr, request.uid,
                                                   ['&',
                                                    ('parent_id', 'child_of', int(category)),
                                                    ('cat_root_id', '=', int(category.cat_root_id))],
                                                   context=request.context)
            # 2.) Extend the product search domain to only show products which are in one or more of the categories
            domain += [('public_categ_ids', 'in', child_categories)]
        else:
            # Only search in non root categories:
            # if a product has no public_categ_ids
            # if a product is in one or more public (non root) categories
            nonroot_categories = category_obj.search(request.cr, request.uid,
                                                     [('cat_root_id.cat_root', '=', False)],
                                                     context=request.context)
            domain += ['|', ('public_categ_ids', '=', False), ('public_categ_ids', 'in', nonroot_categories)]
        return domain

