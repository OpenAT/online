# -*- coding: utf-'8' "-*-"
__author__ = 'mkarrer'
import logging
from openerp import SUPERUSER_ID
from openerp import tools, api
from openerp.osv import osv, orm, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.fso_base.tools.image import resize_to_thumbnail
from openerp.addons.web.http import request

_logger = logging.getLogger(__name__)


# HINT: Since we set this fields on product.template it is not possible to have different values for variants
#       of this product template (= product.product) - which is the intended use-case and ok ;)
class product_template(osv.Model):
    _inherit = "product.template"

    def _get_parallax_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.parallax_image,
                                                            big_name='parallax_image',
                                                            medium_name='parallax_image_medium',
                                                            small_name='parallax_image_small',
                                                            avoid_resize_medium=True)
        return result

    def _set_parallax_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'parallax_image': value}, context=context)

    def _get_square_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            # need to return also an dict for the image like result[1] = {'image_square': base_64_data}
            result[obj.id] = {'image_square': False}
            if obj.image:
                # Get x and y size from website config
                # HINT: Only one Webpage allowed in odoo 8 ;) so [0] is ok
                website = self.pool.get('website').search(cr, uid, [], context=context)[0]
                website = self.pool.get('website').browse(cr, uid, website, context=context)
                x = website.square_image_x or 440
                y = website.square_image_y or 440
                result[obj.id] = {'image_square': resize_to_thumbnail(img=obj.image, box=(x, y),)}
        return result

    def _set_square_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': value}, context=context)

    # OVERRIDE orignal image functional fields to store full size images
    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': value}, context=context)

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image, avoid_resize_medium=True)
        return result

    _columns = {
        # EXTRA FIELDS
        'format': fields.char(string="Format"),
        'webshop_download_file': fields.binary(string="WebShop Download File"),
        'webshop_download_file_name': fields.char(string="WebShop Download File Name"),

        # BEHAVIOUR
        'simple_checkout': fields.boolean('Simple Checkout'),
        # WARNING: DEPRECATED Will be replaced by fs_product_type in addon fso_base
        'fs_workflow': fields.selection([('product', 'Product'),
                                        ('donation', 'Donation')],
                                        string="Fundraising Studio Workflow"),

        # PRODUCT LISTINGS
        'hide_price': fields.boolean('Hide Price in Shop overview Pages'),
        'do_not_link': fields.boolean('Do not link product in cart and product listings'),

        # PRODUCT PAGE
        'product_page_template': fields.selection([('website_sale.product', 'Default Layout'),
                                                   ('website_sale_donate.ppt_donate', 'Donation Standard with Steps'),
                                                   ('website_sale_donate.ppt_opc', 'Donation One-Page-Checkout'),
                                                   ('website_sale_donate.ppt_ahch', 'Donation Simple with Steps'),
                                                   ('website_sale_donate.ppt_inline_donation',
                                                    'Donation Inline with Steps')],
                                                  string="Product Page Template"),
        'parallax_image': fields.binary(string='Background Parallax Image'),
        'parallax_speed': fields.selection([('static', 'Static'), ('slow', 'Slow')], string='Parallax Speed'),
        'hide_categories': fields.boolean('Hide Categories Navigation'),
        'hide_search': fields.boolean('Hide Search Field'),
        'desc_short_top': fields.html(string='Banner Product Description - Top', translate=True),
        'show_desctop': fields.boolean('Show additional Description above Checkout Panel'),
        'desc_short': fields.html(string='Banner Product Description - Center', translate=True),
        'desc_short_bottom': fields.html(string='Banner Product Description - Bottom', translate=True),
        'show_descbottom': fields.boolean('Show additional Description below Checkout Panel'),
        # Checkoutbox in Product Page
        'hide_payment': fields.boolean('Hide complete Checkout Panel'),
        'hide_image': fields.boolean('Hide Image in Checkout Panel'),
        'hide_salesdesc': fields.boolean('Hide Text in Checkout Panel'),
        'variants_as_list': fields.boolean('Show Variants as a List of Products'),
        'hide_quantity': fields.boolean('Hide Product-Quantity-Selector in CP'),
        'hide_amount_title': fields.boolean('Hide Amount Title'),
        'amount_title': fields.char('Amount Title Overwrite', translate=True),
        'price_donate': fields.boolean('Arbitrary Price'),
        'price_donate_min': fields.integer(string='Minimum Arbitrary Price'),
        'price_suggested_ids': fields.one2many('product.website_price_buttons', 'product_id',
                                               string='Suggested Donation-Values', copy=True),
        # DEPRECATED payment_interval_ids only left here for downward compatibility
        'payment_interval_ids': fields.many2many('product.payment_interval', string='Payment Intervals'),
        # PAYMENT INTERVAL
        'payment_interval_default': fields.many2one('product.payment_interval', string='Default Payment Interval'),
        'payment_interval_as_selection': fields.boolean(string='Payment Interval as Selection List'),
        'payment_interval_lines_ids': fields.one2many('product.payment_interval_lines', 'product_id',
                                               string='Payment Intervals', copy=True),
        'button_addtocart_text': fields.char('Add-To-Cart Button Text', size=30, translate=True),
        'hide_panelfooter': fields.boolean('Hide Checkout Panel Footer'),

        # IMAGE HELPER
        'image_square': fields.function(_get_square_image, fnct_inv=_set_square_image,
            string="Square Image (Auto crop and zoom)", type="binary", multi="_get_square_image",
            store={'product.template': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10)}),
        'parallax_image_medium': fields.function(_get_parallax_image, fnct_inv=_set_parallax_image,
            string="Background Parallax Image", type="binary", multi="_get_parallax_image",
            store={
                'product.template': (lambda self, cr, uid, ids, c={}: ids, ['parallax_image'], 10),
            },
            help="Medium-sized image of the background. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved, "\
                 "only when the image exceeds one of those sizes. Use this field in form views or some kanban views."),
        # Override of the original image functional fields to store full size images!
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store={
                'product.template': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of the product. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved, "\
                 "only when the image exceeds one of those sizes. Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'product.template': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of the product. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
        # FRST Groups frst.zgruppedetail
        # ATTENTION: TODO: Check if the domain works because 'sosync_fs_id' is only known after fso_sosnync which
        #                  can not be a dependency of website_sale_donate!
        # HINT: 40200 = Vertragsart, 40300 = Patenart, 40700 = Mitgliedsbeitrag
        'zgruppedetail_ids': fields.many2many('frst.zgruppedetail', string='Fundraising Studio Groups',
                                              domain="[('gui_anzeigen', '=', True),"
                                                     " ('zgruppe_id.sosync_fs_id','in', [40200, 40300, 40700])]"),

    }
    _defaults = {
        'parallax_speed': 'slow',
        'price_donate': True,
        'price_donate_min': 0,
        'hide_quantity': True,
        'product_page_template': 'website_sale_donate.ppt_donate',
    }

    def init(self, cr, context=None):
        # HINT: Since we use the old API search does not return a recordset therefore we need browse too
        products = self.browse(cr, SUPERUSER_ID, self.search(cr, SUPERUSER_ID, []))
        for product in products:
            if not product.product_page_template:
                product.write({"product_page_template": 'website_sale_donate.ppt_donate'})


class product_template_onchange(osv.osv):
    _inherit = 'product.template'

    @api.onchange('price_donate')
    def _set_hide_quantity(self):
        if self.price_donate:
            self.hide_quantity = True


# Extra fields for the created invoices
class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    _columns = {
        'wsd_cat_root_id': fields.many2one('product.public.category', 'RootCateg.', on_delete='set null', copy=False),
        'wsd_so_id': fields.many2one('sale.order', 'Sale Order', on_delete='set null', copy=False),
        'wsd_payment_acquirer_id': fields.many2one('payment.acquirer', 'Payment Acquirer', on_delete='set null', copy=False),
        'wsd_payment_tx_id': fields.many2one('payment.transaction', 'Transaction', on_delete='set null', copy=False),
    }


# Extend sale.order.line to be able to store price_donate and payment interval information
class sale_order_line(osv.Model):
    _inherit = "sale.order.line"
    _columns = {
        # Transferred from context or kwargs and copied to 'price_unit' field by _cart_update()
        'price_donate': fields.float('Donate Price', digits_compute=dp.get_precision('Product Price'), ),
        # Transferred from product by _cart_update()
        'payment_interval_id': fields.many2one('product.payment_interval', string='Payment Interval ID'),
        'payment_interval_name': fields.text('Payment Interval Name'),
        'payment_interval_xmlid': fields.text('Payment Interval Name'),
        # Transferred from context or kwargs by _cart_update()
        'fs_ptoken': fields.text('FS Partner Token', readonly=True),
        'fs_origin': fields.char('FS Partner Token Origin', help="The Fundraising Studio activity ID", readonly=True),
        # FRST Groups frst.zgruppedetail, transferred from product by _cart_update()
        'zgruppedetail_ids': fields.many2many('frst.zgruppedetail', string='Fundraising Studio Groups', readonly=True),
        # Copy fs_product_type to sale order line by _cart_update()
        'fs_product_type': fields.char('FRST product type', readonly=True)
    }


class sale_order(osv.Model):
    _inherit = "sale.order"

    # Todo extend _prepare_invoice to add extra fields for reports and statistics
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        res = super(sale_order, self)._prepare_invoice( cr=cr, uid=uid, order=order, lines=lines, context=context)
        # TODO add cat_root_id, wsd_cat_id, wsd_so_id, wsd_payment_acquirer_id, wsd_payment_tx_id
        if order:
            invoice_vals = {
                'wsd_cat_root_id': order.cat_root_id.id if order.cat_root_id else None,
                'wsd_so_id': order.id,
                'wsd_payment_acquirer_id': order.payment_acquirer_id.id if order.payment_acquirer_id else None,
                'wsd_payment_tx_id': order.payment_tx_id.id if order.payment_tx_id else None,
            }
            res.update(invoice_vals)
        return res

    def _website_product_id_change(self, cr, uid, ids, order_id, product_id, qty=0, line_id=None, context=None):
        context = context or {}
        res = super(sale_order, self)._website_product_id_change(cr, uid, ids, order_id, product_id, qty=qty,
                                                                 line_id=line_id, context=context)
        if context.get('price_donate'):
            res.update({'price_unit': context.get('price_donate')})
        return res

    # extend _cart_update to write price_donate and payment_interval to the sale.order.line if existing in kwargs
    def _cart_update(self, cr, uid, ids, product_id=None, line_id=None, add_qty=0, set_qty=0, context=None, **kwargs):

        # Try to recalculate all functional fields on write
        context = context or {}
        context = dict(context, recompute=True)
        context = dict(context, no_store_function=True)

        # Helper: Check if Argument is a Number and greater than zero
        def is_float_gtz(number=''):
            try:
                # if float conversion fails = except: return False
                # or if number is smaller than zero also return False
                if float(number) <= 0:
                    return False
                return True
            except:
                return False

        # Set the Quantity always to 1 or 0 if hide_quantity is set
        # HINT: We have to use product.product NOT product.template because it could be a product variant
        #       _cart_update always gets the product.product id !!! from the template!
        product = self.pool.get('product.product').browse(cr, SUPERUSER_ID, product_id, context=context)
        if product.hide_quantity:
            if add_qty >= 0:
                set_qty = 1
            else:
                set_qty = 0

        # Update context with price_donate
        price_donate = kwargs.get('price_donate')
        if price_donate:
            context.update({'price_donate': price_donate})

        # Update or create the sale order line
        cu = super(sale_order, self)._cart_update(cr, uid, ids,
                                                  product_id, line_id, add_qty, set_qty, context=context, **kwargs)

        # Remove price_donate from the context again
        if context.get('price_donate'):
            context.pop('price_donate', None)

        # Get the updated or created sale order line
        line_id = cu.get('line_id')
        sol_obj = self.pool.get('sale.order.line')
        sol = sol_obj.browse(cr, SUPERUSER_ID, line_id, context=context)

        quantity = cu.get('quantity')
        payment_interval_id = kwargs.get('payment_interval_id')

        # Update the sale order line values:
        # 'price_donate', 'payment_interval_id', 'zgruppedetail_ids', 'fs_product_type', TODO: ptoken?!?
        # HINT: sol.exists() is checked in case that so line was unlinked in inherited _cart_update
        if quantity > 0 and sol.exists():

            # If we come from a product page price_donate may be in the kwargs and if so we write it to so line
            # SECURITY: Make sure price_donate is some sort of float (real float conversion will be done by orm)
            # SECURITY: make sure price_donate checkbox is set in related product
            # VALIDATION: Make Sure price_donate is not lower than price_donate_min set in the product
            #             if it is lower then do not set price_donate = do not alter price_unit
            if price_donate \
                    and is_float_gtz(price_donate) \
                    and sol.product_id.price_donate \
                    and price_donate >= sol.product_id.price_donate_min:
                sol.price_donate = price_donate
                # sol_obj.write(cr, SUPERUSER_ID, [line_id], {'price_donate': price_donate, }, context=context)

            # no matter where we come from if so line already exists and has filled price_donate field we have to
            # update the price_unit again to not loose our custom price price_donate
            if sol.price_donate:
                _logger.info('_cart_update(): sale_order_line: copy price_donate %s to price_unit %s'
                             '' % (str(sol.price_donate), str(sol.price_unit)))
                sol.price_unit = sol.price_donate
                # sol_obj.write(cr, SUPERUSER_ID, [line_id], {'price_unit': sol.price_donate, }, context=context)

            # If Payment Interval is found in kwargs write it to the so line
            # Todo: SECURITY Check if payment_interval_id: is an int and if it is available in product.payment_interval
            if payment_interval_id:
                # Todo: CATCH if int conversion fails (like float above)
                sol.payment_interval_id = int(payment_interval_id)
                if sol.payment_interval_id.exists():
                    sol.payment_interval_name = sol.payment_interval_id.name
                    sol.payment_interval_xmlid = sol.payment_interval_id.get_metadata()[0]['xmlid']

            # Copy zgruppedetail_ids (frst.zgruppedetail, fso_frst_groups) from the product to the sale_order_line
            if sol.product_id and sol.product_id.zgruppedetail_ids:
                _logger.info('_cart_update(): copy zgruppedetail_ids from sol.product_id.zgruppedetail_ids '
                             'to sol.zgruppedetail_ids')
                sol.zgruppedetail_ids = sol.product_id.zgruppedetail_ids
            else:
                sol.zgruppedetail_ids = False

            # Copy fs_product_type to sale_order_line
            if sol.product_id and sol.product_id.fs_product_type:
                _logger.info('_cart_update(): copy fs_product_type from sol.product_id.fs_product_type '
                             'to sol.fs_product_type')
                sol.fs_product_type = sol.product_id.fs_product_type
            else:
                sol.fs_product_type = False

            # REMOVE ALL OTHER SALE ORDER LINES WHERE INDIVIDUAL (PER PRODUCT) CONFIGURATIONS DO NOT MATCH
            # 'PAYMENT METHOD', 'CHECKOUT FIELDS' OR 'STEPS INDICATOR' WITH THE CURRENT SALE ORDER LINE
            order = sol.order_id
            for l in order.website_order_line:
                if l.exists() and l.id != sol.id:

                    # Acquirer config mismatch
                    if product.product_acquirer_lines_ids != l.product_id.product_acquirer_lines_ids:
                        product_acquirer_ids = [] if not product.product_acquirer_lines_ids \
                            else product.product_acquirer_lines_ids.ids
                        sol_acquirer_ids = [] if not l.product_id.product_acquirer_lines_ids \
                            else l.product_id.product_acquirer_lines_ids.ids
                        # HINT: s ^ t = new set with elements in either s or t but not both
                        if bool(set(product_acquirer_ids) ^ set(sol_acquirer_ids)):
                            _logger.info('_cart_update(): Remove sale order line (ID: %s) from SO (ID: %s) because '
                                         'acquirer configurations do not match' % (l.id, order.id))
                            sol_obj.unlink(cr, SUPERUSER_ID, [l.id], context=context)
                            continue

                    # Checkout steps mismatch
                    if product.step_indicator_setup and l.product_id.step_indicator_setup:
                        if any(product[sf] != l.product_id[sf] for sf in product.product_tmpl_id._step_config_fields):
                            _logger.info('_cart_update(): Remove sale order line (ID: %s) from SO (ID: %s) because '
                                         'checkout steps configurations do not match' % (l.id, order.id))
                            sol_obj.unlink(cr, SUPERUSER_ID, [l.id], context=context)
                            continue

                    # Checkout fields mismatch (billing fields)
                    if product.checkout_form_id != l.product_id.checkout_form_id:
                        _logger.info('_cart_update(): Remove sale order line (ID: %s) from SO (ID: %s) because '
                                     'checkout fields configurations do not match' % (l.id, order.id))
                        sol_obj.unlink(cr, SUPERUSER_ID, [l.id], context=context)
                        continue

        return cu

    # Check if there are any recurring transaction products in the sale order
    def _has_recurring(self, cr, uid, ids, field_name, arg, context=None):
        # HINT: functional Fields have to return an dict!
        #       https://doc.odoo.com/6.0/developer/2_5_Objects_Fields_Methods/field_type/
        res = {}

        # Get th ID of payment interval with xml_id once_only to use it in the search domain
        # HINT: get_object takes the module name where the record was created and NOT the model name as expected!
        model_data_obj = self.pool.get('ir.model.data')
        pi_once_only_id = model_data_obj.get_object(cr, uid, 'website_sale_donate', 'once_only').id

        # check if we can find a related SO line with an payment interval other than None or once_only
        for order in self.browse(cr, uid, ids, context=context):
            domain = [('order_id', '=', order.id), ('payment_interval_id', '!=', pi_once_only_id)]
            if self.pool.get('sale.order.line').search(cr, SUPERUSER_ID, domain, context=context):
                res[order.id] = True
            else:
                res[order.id] = False

        return res

    _columns = {
        'has_recurring': fields.function(_has_recurring,
                                         type='boolean',
                                         string='Has order lines with recurring transactions'),
    }

    # Use a custom e-mail template from fso_base if it exists for the send quotation e-mail wizard.
    # HINT: action_quotation_send is already overwritten by addon "website_quote" and "portal_sale"!
    def action_quotation_send(self, cr, uid, ids, context=None,
                              email_template_addon='fso_base',
                              email_template_name='email_template_webshop'):
        """ extend the interface of action_quotation_send to call it for a custom email template """
        action_dict = super(sale_order, self).action_quotation_send(cr, uid, ids, context=context)
        try:
            template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid,
                                                                              email_template_addon,
                                                                              email_template_name)[1]
            if template_id:
                ctx = action_dict['context']
                ctx['default_template_id'] = template_id
                ctx['default_use_template'] = True
        except Exception:
            _logger.warning("Custom Payment Status E-Mail Template not found! Check dadi payment provider code!"
                            "(website_sale_donate > action_qutation_send)")
            pass

        return action_dict


# CROWD FUNDING EXTENSIONS
# ========================
class product_product_crowd_funding(osv.Model):
    _inherit = 'product.product'

    def _sold_total(self, cr, uid, ids, field_name, arg, context=None):
        r = dict.fromkeys(ids, 0)

        # HINT: sale.report is based on sale.order.lines. States are defined in sale.report at field state.
        #       see: odoo/addons/sale/report/sale_report.py
        domain = [('product_id', 'in', ids), ('state', 'in', ['confirmed', 'done'])]
        fields = ['product_id', 'price_total']
        groupby = ['product_id']
        for group in self.pool['sale.report'].read_group(cr, SUPERUSER_ID, domain, fields, groupby, context=context):
            r[group['product_id'][0]] = group['price_total']

        # HINT: functional fields functions have to return a dict in form of {id: value}
        return r

    def action_view_sales_sold_total(self, cr, uid, ids, context=None):
        result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree',
                                                            raise_if_not_found=True)
        result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
        domain = [
            ('state', 'in', ["confirmed", "done"]),
            ('product_id', 'in', ids),
        ]
        result['domain'] = str(domain)
        return result

    _columns = {
        'sold_total': fields.function(_sold_total, string='# Sold Total', type='float'),
        # Add Download Field and name for the product variant
        'webshop_download_file': fields.binary(string="WebShop Download File"),
        'webshop_download_file_name': fields.char(string="WebShop Download File Name"),
    }


class product_template_crowd_funding(osv.Model):
    _inherit = 'product.template'

    def _sold_total(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        for template in self.browse(cr, SUPERUSER_ID, ids, context=context):
            res[template.id] = sum([p.sold_total for p in template.product_variant_ids])
        return res

    def _funding_reached(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        for ptemplate in self.browse(cr, SUPERUSER_ID, ids, context=context):
            try:
                res[ptemplate.id] = int(round(ptemplate.sold_total / (ptemplate.funding_goal / 100)))
            except:
                res[ptemplate.id] = int(0)
        return res

    def action_view_sales_sold_total(self, cr, uid, ids, context=None):
        act_obj = self.pool.get('ir.actions.act_window')
        mod_obj = self.pool.get('ir.model.data')
        # find the related product.product ids
        product_ids = []
        for template in self.browse(cr, uid, ids, context=context):
            product_ids += [x.id for x in template.product_variant_ids]
        domain = [
            ('state', 'in', ["confirmed", "done"]),
            ('product_id', 'in', product_ids),
        ]
        # get the tree view
        result = mod_obj.xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree', raise_if_not_found=True)
        result = act_obj.read(cr, uid, [result], context=context)[0]
        # add the search domain
        result['domain'] = str(domain)
        return result

    # Hack because i could not find a way to browse res.partner.name in qweb template - always error 403 access rights
    # The positive side effect is better security since no one can browse res.partner fully!
    def _get_name(self, cr, uid, ids, flds, args, context=None):
        res = dict.fromkeys(ids, 0)
        for ptemplate in self.browse(cr, SUPERUSER_ID, ids, context=context):
            if ptemplate.funding_user:
                res[ptemplate.id] = ptemplate.funding_user.name
            else:
                res[ptemplate.id] = False
        return res

    _columns = {
        'sold_total': fields.function(_sold_total, string='# Sold Total', type='float'),
        'funding_goal': fields.float(string='Funding Goal'),
        'funding_desc': fields.html(string='Funding Description', translate=True),
        'funding_reached': fields.function(_funding_reached, string='Funding reached in %', type='integer'),
        'funding_user': fields.many2one('res.partner', string='Funding-Campaign User'),
        'funding_user_name': fields.function(_get_name, string="Funding-Campaign User Name", type='char'),

        'hide_fundingtextinlist': fields.boolean('Hide Funding-Text in Overview-Pages'),
        'hide_fundingbarinlist': fields.boolean('Hide Funding-Bar in Overview-Pages'),
        'hide_fundingtextincp': fields.boolean('Hide Funding-Text in Checkout-Panel'),
        'hide_fundingbarincp': fields.boolean('Hide Funding-Bar in Checkout-Panel'),
        'hide_fundingtext': fields.boolean('Hide Funding-Text in Page'),
        'hide_fundingbar': fields.boolean('Hide Funding-Bar in Page'),
        'hide_fundingdesc': fields.boolean('Hide Funding-Description in Page'),
    }
