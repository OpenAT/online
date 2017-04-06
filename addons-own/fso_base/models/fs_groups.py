# -*- coding: utf-8 -*-
import logging
# Old API
from openerp.osv import osv, fields, expression
# New API
from openerp import fields as new_api_fields
from openerp import models
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


# Fundraising Studio Groups
class FSGroups(models.Model):
    _name = 'fs.group'
    _description = 'Fundraising Studio Groups'

    name = new_api_fields.Char(string="FS Group Name")


# Add Fundraising Studio Groups to product.template
# and make override possible in product.product (= product variant)
# TODO: Refactor to new API
class ProductTemplate(osv.osv):
    _inherit = 'product.template'

    # Return False if there are product variants else return product_variant_fs_group_ids
    # from the related product.product
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
