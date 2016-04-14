# -*- coding: utf-'8' "-*-"
__author__ = 'mkarrer'

from openerp import SUPERUSER_ID
from openerp import tools, api
from openerp.osv import osv, orm, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.base_tools.image import resize_to_thumbnail


# Additional fields for the web checkout
class res_partner(osv.Model):
    _inherit = 'res.partner'

    _columns = {
        # Vorname (wird dann in das feld name geschrieben)
        'fore_name_web': fields.char(string='Fore Name Web'),
        # Firmenname
        'company_name_web': fields.char(string='Company Name Web'),
        # Hausnummer
        'street_number_web': fields.char(string='Street Number Web'),
        # Postfach
        'post_office_box_web': fields.char(string='Post Office Box Web'),
        # Newsletteranmeldung event. auch Opt Out
        'newsletter_web': fields.boolean(string='Newsletter Web'),
        # Spendenquittung, Spendenbestaetigung fuer die Steuer
        'donation_receipt_web': fields.boolean(string='Donation Receipt Web'),
    }

class product_website_price_buttons(osv.Model):
    """Suggested Donations-Value-Buttons"""
    _name = 'product.website_price_buttons'
    _description = 'Product Website Price Buttons'
    _order = 'sequence, name'

    _columns = {
        'sequence': fields.integer('Sequence'),
        'product_id': fields.many2one('product.template', string='Product', required=True, ondelete='cascade'),
        'name': fields.char(string='Name'),
        'amount': fields.float(string='Amount', required=True),
        'css_classes': fields.char(string='CSS classes'),
    }

    _defaults = {
        'sequence': 1000,
    }


class website_checkout_billing_fields(osv.Model):
    """res.partner billing fields for the website checkout form"""
    _name = 'website.checkout_billing_fields'
    _description = 'Checkout Billing Fields'
    _order = 'sequence, res_partner_field_id'

    _columns = {
        'sequence': fields.integer('Sequence', help='Sequence number for ordering'),
        'show': fields.boolean(string='Show', help='Show field in webpage'),
        'res_partner_field_id': fields.many2one('ir.model.fields',
                                                string="res.partner Field",
                                                domain="[('model_id.model', '=', 'res.partner')]",
                                                required=True),
        'mandatory': fields.boolean(string='Mandatory'),
        'label': fields.char(string='Label', translate=True),
        'placeholder': fields.char(string='Placeholder Text', translate=True),
        'validation_rule': fields.char(string='Validation Rule'),
        'css_classes': fields.char(string='CSS classes'),
        'clearfix': fields.boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field'),
    }

    _defaults = {
        'active': True,
        'sequence': 1000,
        'css_classes': 'col-lg-6',
    }

class website_checkout_shipping_fields(osv.Model):
    """res.partner shipping fields for the website checkout form"""
    _name = 'website.checkout_shipping_fields'
    _description = 'Checkout Shipping Fields'
    _order = 'sequence, res_partner_field_id'

    _columns = {
        'sequence': fields.integer('Sequence', help='Sequence number for ordering'),
        'show': fields.boolean(string='Show', help='Show field in webpage'),
        'res_partner_field_id': fields.many2one('ir.model.fields',
                                                string="res.partner Field",
                                                domain="[('model_id.model', '=', 'res.partner')]",
                                                required=True),
        'mandatory': fields.boolean(string='Mandatory'),
        'label': fields.char(string='Label', translate=True),
        'placeholder': fields.char(string='Placeholder Text', translate=True),
        'validation_rule': fields.char(string='Validation Rule'),
        'css_classes': fields.char(string='CSS classes'),
        'clearfix': fields.boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field'),
    }

    _defaults = {
        'active': True,
        'sequence': 1000,
        'css_classes': 'col-lg-6',
    }


# Mandatory fields setting for checkout form
# HINT: used in website_sale_donate main.py -> _get_mandatory_*_fields
# ATTENTION: You must use *_mandatory_bill and *_mandatory_ship after the field name! (to later identify the fields)
class website_sale_donate_settings(osv.Model):
    _inherit = 'website'
    _columns = {
        # Checkout Pages Headers
        'cart_page_header': fields.char(string='Cart Page Main Header', translate=True),
        'checkout_page_header': fields.char(string='Checkout Page Main Header', translate=True),
        'payment_page_header': fields.char(string='Payment Page Main Header', translate=True),
        'confirmation_page_header': fields.char(string='Confirmation Page Main Header', translate=True),
        # Checkout Steps Indicator
        'cart_indicator': fields.char(string='Indicator Cart', translate=True),
        'checkout_indicator': fields.char(string='Indicator Checkout', translate=True),
        'payment_indicator': fields.char(string='Indicator Payment', translate=True),
        'confirmation_indicator': fields.char(string='Indicator Confirmation', translate=True),
        # small-cart-header
        'small_cart_title': fields.char(string='Small Cart Title', translate=True),
        # Section h3's for the custom checkout form
        'amount_title': fields.char(string='Amount (Checkoutbox) Form-Title', translate=True),
        'checkout_title': fields.char(string='Your Data Form-Title', translate=True),
        'delivery_title': fields.char(string='Delivery-Option Form-Title', translate=True),
        'payment_title': fields.char(string='Payment-Option Form-Title', translate=True),
        # Buttons
        'button_login': fields.char(string='Login Button', translate=True),
        'button_logout': fields.char(string='Logout Button', translate=True),
        'button_back_to_page': fields.char(string='Back to Page Button', translate=True),
        'button_cart_to_data': fields.char(string='Cart to Data Button', translate=True),
        'button_data_to_payment': fields.char(string='Data to Payment Button', translate=True),
        # Behaviour
        'country_default_value': fields.many2one('res.country', string='Default country for checkout page'),
        'acquirer_default': fields.many2one('payment.acquirer', string='Default Payment Method'),
        'payment_interval_default': fields.many2one('product.payment_interval', string='Default Payment Interval'),
        'add_to_cart_stay_on_page': fields.boolean(string='Add to Cart and stay on Page'),
        'checkout_show_login_button': fields.boolean(string='Show Login Button on Checkout Page'),
        'one_page_checkout': fields.boolean(string='One-Page-Checkout'),
        'hide_shipping_address': fields.boolean(string='Hide Shipping Address'),
        'hide_delivery_methods': fields.boolean(string='Hide Delivery Methods'),
        # Global Fields for Snippets
        'checkoutbox_footer': fields.html(string='Global Footer for the Checkoutbox'),
        'cart_page_top': fields.html(string='Cart Page Top Snippet Dropping Area'),
        'cart_page_bottom': fields.html(string='Cart Page Bottom Snippet Dropping Area'),
        'checkout_page_top': fields.html(string='Checkout Page Top Snippet Dropping Area'),
        'checkout_page_bottom': fields.html(string='Checkout Page Bottom Snippet Dropping Area'),
        'payment_page_top': fields.html(string='Payment Page Top Snippet Dropping Area'),
        'payment_page_bottom': fields.html(string='Payment Page Bottom Snippet Dropping Area'),
        'confirmation_page_top': fields.html(string='Payment Page Top Snippet Dropping Area'),
        'confirmation_page_bottom': fields.html(string='Payment Page Bottom Snippet Dropping Area'),
        # Square Image Dimensions
        'square_image_x': fields.integer(string='Product SquareImage x-Size in Pixel'),
        'square_image_y': fields.integer(string='Product SquareImage y-Size in Pixel'),
    }
    _defaults = {
        'square_image_x': 400,
        'square_image_y': 400,
    }


class payment_interval(osv.Model):
    _name = 'product.payment_interval'
    _order = 'sequence, name'
    _columns = {
        'sequence': fields.integer('Sequence'),
        'name': fields.text('Payment Interval', required=True, translate=True),
        # DEPRECATED product_template_ids only left here for downward compatibility
        'product_template_ids': fields.many2many('product.template', string='Products'),
        'payment_interval_lines_ids': fields.one2many('product.payment_interval_lines', 'payment_interval_id',
                                               string='Payment Interval Lines'),
    }
    _defaults = {
        'sequence': 1000,
    }

payment_interval()


class payment_interval_lines(osv.Model):
    _name = 'product.payment_interval_lines'
    _order = 'sequence, payment_interval_id'
    _columns = {
        'sequence': fields.integer('Sequence'),
        'payment_interval_id': fields.many2one('product.payment_interval', string='Payment Interval', required=True),
        'product_id': fields.many2one('product.template', string='Product', required=True),
    }
    _defaults = {
        'sequence': 1000,
    }


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

        # BEHAVIOUR
        'simple_checkout': fields.boolean('Simple Checkout'),

        # PRODUCT LISTINGS
        'hide_price': fields.boolean('Hide Price in Shop overview Pages'),
        'do_not_link': fields.boolean('Do not link product in cart and product listings'),

        # PRODUCT PAGE
        'product_page_template': fields.selection([('website_sale.product', 'Default Layout'),
                                                   ('website_sale_donate.ppt_donate', 'Donation Layout'),
                                                   ('website_sale_donate.ppt_opc', 'One-Page-Checkout Layout'),
                                                   ('website_sale_donate.ppt_ahch', 'Simple Layout')],
                                                  string="Product Page Template"),
        'parallax_image': fields.binary(string='Background Parallax Image'),
        'parallax_speed': fields.selection([('static', 'Static'), ('slow', 'Slow')], string='Parallax Speed'),
        'hide_categories': fields.boolean('Hide Categories Navigation'),
        'hide_search': fields.boolean('Hide Search Field'),
        'desc_short_top': fields.html(string='Banner Product Description - Top'),
        'show_desctop': fields.boolean('Show additional Description above Checkout Panel'),
        'desc_short': fields.html(string='Banner Product Description - Center'),
        'desc_short_bottom': fields.html(string='Banner Product Description - Bottom'),
        'show_descbottom': fields.boolean('Show additional Description below Checkout Panel'),
        # Checkoutbox in Product Page
        'hide_payment': fields.boolean('Hide complete Checkout Panel'),
        'hide_image': fields.boolean('Hide Image in Checkout Panel'),
        'hide_salesdesc': fields.boolean('Hide Text in Checkout Panel'),
        'variants_as_list': fields.boolean('Show Variants as a List of Products'),
        'hide_quantity': fields.boolean('Hide Product-Quantity-Selector in CP'),
        'price_donate': fields.boolean('Arbitrary Price'),
        'price_donate_min': fields.integer(string='Minimum Arbitrary Price'),
        'price_suggested_ids': fields.one2many('product.website_price_buttons', 'product_id',
                                               string='Suggested Donation-Values'),
        # DEPRECATED payment_interval_ids only left here for downward compatibility
        'payment_interval_ids': fields.many2many('product.payment_interval', string='Payment Intervals'),
        'payment_interval_default': fields.many2one('product.payment_interval', string='Default Payment Interval'),
        'payment_interval_lines_ids': fields.one2many('product.payment_interval_lines', 'product_id',
                                               string='Payment Intervals'),
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


# Extend sale.order.line to be able to store price_donate and payment interval information
class sale_order_line(osv.Model):
    _inherit = "sale.order.line"
    _columns = {
        'price_donate': fields.float('Donate Price', digits_compute=dp.get_precision('Product Price'), ),
        'payment_interval_id': fields.many2one('product.payment_interval', string='Payment Interval ID'),
        'payment_interval_name': fields.text('Payment Interval Name'),
        'payment_interval_xmlid': fields.text('Payment Interval Name'),
    }


class sale_order(osv.Model):
    _inherit = "sale.order"

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
        # HINT: We have to use product.product NOT product.temaplate beacuse it could be a product variant
        #       _cart_update always gets the product.product id !!! from the template!
        if self.pool.get('product.product').browse(cr, SUPERUSER_ID, product_id, context=context).hide_quantity:
            if add_qty >= 0:
                set_qty = 1
            else:
                set_qty = 0

        # Update context with price_donate and call super
        price_donate = kwargs.get('price_donate')
        if price_donate:
            context.update({'price_donate': price_donate})
        cu = super(sale_order, self)._cart_update(cr, uid, ids,
                                                  product_id, line_id, add_qty, set_qty, context=context, **kwargs)
        if context.get('price_donate'):
            context.pop('price_donate', None)

        payment_interval_id = kwargs.get('payment_interval_id')
        line_id = cu.get('line_id')
        quantity = cu.get('quantity')
        sol_obj = self.pool.get('sale.order.line')
        sol = sol_obj.browse(cr, SUPERUSER_ID, line_id, context=context)

        # sol.exists() is checked in case that so line was unlinked in inherited _cart_update
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
                sol.price_unit = sol.price_donate
                # sol_obj.write(cr, SUPERUSER_ID, [line_id], {'price_unit': sol.price_donate, }, context=context)

            # TODO: Hack: for no obvious reason functional fields do net get updated on sale.order.line writes ?!? so we do it manually!
            # Sadly not working
            # sol_obj.write(cr, SUPERUSER_ID, [line_id], {'price_subtotal': sol_obj._amount_line(cr, SUPERUSER_ID, [line_id], None, None, context=context), 'price_reduce': sol_obj._get_price_reduce(cr, SUPERUSER_ID, [line_id], None, None, context=context), }, context=context)


            # If Payment Interval is found in kwargs write it to the so line
            # Todo: SECURITY Check if payment_intervall_id: is an int and if it is available in product.payment_interval
            if payment_interval_id:
                # Todo: CATCH if int conversion fails (like float above)
                sol.payment_interval_id = int(payment_interval_id)
                if sol.payment_interval_id.exists():
                    sol.payment_interval_name = sol.payment_interval_id.name
                    sol.payment_interval_xmlid = sol.payment_interval_id.get_metadata()[0]['xmlid']

                    # ToDo: Try to browse and write to the sales order to update relevant fields
                    # so_obj = self.pool.get('sale.order')
                    # so = so_obj.browse(cr, SUPERUSER_ID, sol.order_id.id, context=context)
                    # so.write(cr, SUPERUSER_ID, {}, context=context)

            # Add Root CatID and root cat id to the so-line if they are in kwargs
            # TODO: this code should be in website_sale_categories!!!


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


# Add recurring_transactions, image_field and sequence to payment.acquirer
# HINT: We also add a functional field to sale_order "has_recurring_transactions" type bool - This field is true
#       if there are any recurring transaction products other than  "einmailig" which has an xml_id of
#       "once_only" in this sale.order
class PaymentAcquirer(osv.Model):
    _inherit = 'payment.acquirer'
    _order = 'sequence, name'
    _columns = {
        'sequence': fields.integer('Sequence'),
        'recurring_transactions': fields.boolean('Recurring Transactions'),
        'acquirer_icon': fields.binary("Acquirer Icon", help="Acquirer Icon 120x90 PNG 32Bit"),
        'submit_button_text': fields.char(string='Submit Button Text', translate=True,
                                          help='Only works in FS-Online Payment Methods'),
        'submit_button_class': fields.char(string='Submit Button CSS classes',
                                           help='Only works in FS-Online Payment Methods'),
        'redirect_url_after_form_feedback': fields.char(string='Redirect URL after PP Form-Feedback',
                                                        help='Redirect to this URL after processing the Answer of the Payment Provider instead of /shop/confirmation_static'),
        'do_not_send_status_email': fields.boolean('Do not send Confirmation E-Mails on TX-State changes.',
                                                   help='Will not send website_sale_payment_fix.email_template_webshop'),
    }
    _defaults = {
        'recurring_transactions': False,
        'sequence': 1000,
    }


# CROWD FUNDING EXTENSIONS
# ========================
class product_product(osv.Model):
    _inherit = 'product.product'

    def _sold_total(self, cr, uid, ids, field_name, arg, context=None):
        r = dict.fromkeys(ids, 0)
        domain = [
            ('state', 'in', ['waiting_date', 'progress', 'manual', 'shipping_except', 'invoice_except', 'done']),
            ('product_id', 'in', ids),
        ]
        for group in self.pool['sale.report'].read_group(cr, SUPERUSER_ID, domain, ['product_id', 'price_total'],
                                                         ['product_id'], context=context):
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
    }


class product_template(osv.Model):
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
