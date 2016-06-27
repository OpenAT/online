# -*- coding: utf-8 -*-

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

import logging
from openerp.osv import osv, fields, expression
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class FSGroups(osv.osv):
    _name = 'fs.group'
    _description = 'Fundraising Studio Groups'

    _columns = {
        'name': fields.char("FS Group Name"),
    }


class ProductTemplate(osv.osv):
    _inherit = 'product.template'

    # Return False if there are product variants else return product_variant_fs_group_ids from the related product.product
    def _get_product_variant_fs_group_ids(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)

        for template in self.browse(cr, uid, ids, context=context):
            if template.attribute_line_ids:
                # Product Variants exists
                # Return False
                result[template.id] = False
            else:
                # No Variants (= one default Variant)
                # return product_variant_fs_group_ids from related product.product default variant
                product = self.pool['product.product'].browse(cr, uid,
                                                              template.product_variant_ids.ids[0], context=context)
                result[template.id] = product.product_variant_fs_group_ids

        return result

    # Update product.product field product_variant_fs_group_ids if there are no variants else do nothing
    def _set_product_variant_fs_group_ids(self, cr, uid, id, name, value, args, context=None):
        template = self.browse(cr, uid, id, context=context)

        if not template.attribute_line_ids:
            # No Variants
            # Update the product_variant_fs_group_ids field for related product.product default variant
            # HINT: template.product_variant_ids must be checked in case the template is created just right now and
            #       has no related product variant already
            if template.product_variant_ids:
                product = self.pool['product.product'].browse(cr, uid,
                                                              template.product_variant_ids.ids[0], context=context)
                product.product_variant_fs_group_ids = value
        else:
            raise osv.except_osv(_('Error!'), _('Product variants exist! Please set the FS-Groups there!'))

    _columns = {
        # Always use the product.product "product_variant_fs_group_ids" field
        'fs_group_ids': fields.function(_get_product_variant_fs_group_ids, fnct_inv=_set_product_variant_fs_group_ids,
                                        type="many2many", relation="fs.group",
                                        string='FS Groups (Template)'),
    }


    def create(self, cr, uid, vals, context=None):
        product_template_id = super(ProductTemplate, self).create(cr, uid, vals, context=context)

        related_vals = {}
        if vals.get('fs_group_ids'):
            related_vals['fs_group_ids'] = vals['fs_group_ids']
        if related_vals:
            self.write(cr, uid, product_template_id, related_vals, context=context)

        return product_template_id


class ProductProduct(osv.osv):
    _inherit = 'product.product'

    def _get_fs_groups(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)

        for product in self.browse(cr, uid, ids, context=context):
            result[product.id] = product.product_variant_fs_group_ids

        return result

    def _set_fs_groups(self, cr, uid, id, name, value, args, context=None):
        # If we are a product variant write to product_variant_fs_group_ids else write to product.template fs_group_ids
        product = self.browse(cr, uid, id, context=context)
        product.product_variant_fs_group_ids = value

    _columns = {
        'fs_group_ids': fields.function(_get_fs_groups, fnct_inv=_set_fs_groups,
                                        type="many2many", relation="fs.group",
                                        string='FS Groups (Variant)'),
        'product_variant_fs_group_ids': fields.many2many('fs.group',  string='FS Groups'),
    }

