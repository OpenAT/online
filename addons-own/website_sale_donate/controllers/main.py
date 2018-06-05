# -*- coding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from lxml import etree
from urlparse import urlparse
from datetime import timedelta
from openerp import fields
from openerp.addons.website.models.website import slug

import locale

# import copy
# import requests

# To get a new db connection:
# from openerp.modules.registry import RegistryManager

# import the base controller class to inherit from
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.addons.website_sale.controllers.main import QueryURL

_logger = logging.getLogger(__name__)


class website_sale_donate(website_sale):

    def _get_payment_interval_id(self, product):
        payment_interval_id = False

        # 1. Website-Settings global default payment interval
        if request.website.payment_interval_default:
            payment_interval_id = request.website.payment_interval_default.id
        # 2. DEPRECATED! (but still there for old database-backups compatibility)
        if product.payment_interval_ids:
            payment_interval_id = product.payment_interval_ids[0].id
        # 3. Products first payment_interval_line id
        if product.payment_interval_lines_ids:
            payment_interval_id = product.payment_interval_lines_ids[0].payment_interval_id.id
        # 4. Products default payment interval
        if product.payment_interval_default:
            payment_interval_id = product.payment_interval_default.id

        return payment_interval_id

    # SHOP PAGE: Add last_shop_page to the session
    @http.route()
    def shop(self, page=0, category=None, search='', **post):
        try:
            _logger.warning("shop(): START %s" % request.httprequest)
        except:
            _logger.warning("shop(): START")

        base_url = str(urlparse(request.httprequest.base_url).path)
        request.session['last_shop_page'] = base_url + ('?category='+str(category.id) if category else '')
        request.session['last_page'] = request.session['last_shop_page']

        _logger.warning("shop(): END, return super(website_sale_donate, self).shop(...)")
        return super(website_sale_donate, self).shop(page=page, category=category, search=search, **post)

    # PRODUCT PAGE: Extend the product page render request to include price_donate and payment_interval
    # so we have the same settings for arbitrary price and payment interval as already set by the user in the so line
    # Todo: Would need to update the Java Script of Website_sale to select the correct product variante if it
    #       is already in the current sales order (like i do it for price_donate and payment_interval)
    #       ALSO i need to update the java script that loads the product variant pictures
    # /shop/product/<model("product.template"):product>
    @http.route()
    def product(self, product, category='', search='', **kwargs):
        try:
            _logger.warning("product(): START %s kwargs: \n%s\n" % (request.httprequest, kwargs or None))
        except:
            _logger.warning("product(): START")

        # Make sure category is a valid int or an empty string!
        try:
            category = int(category)
        except:
            category = ''

        # Check visibility
        if not product.active or (not request.website.is_publisher() and not product.website_visible):
                #return request.render('website.page_404', {'path': product.website_url, 'code': '404'})
                return request.registry['ir.http']._handle_exception(AttributeError, 404)

        # Store the current request url in the session for possible returns
        # HINT: html escaping is done by request.redirect so not needed here!
        query = {'category': category, 'search': search}
        query = '&'.join("%s=%s" % (key, val) for (key, val) in query.iteritems() if val)
        request.session['last_page'] = request.httprequest.base_url + '?' + query

        cr, uid, context = request.cr, request.uid, request.context

        # -----------------
        # ONE PAGE CHECKOUT Start
        # -----------------
        # HINT: This is needed since the regular route cart_update is not called in case of one-page-checkout
        if request.httprequest.method == 'POST' \
                and product.product_page_template == u'website_sale_donate.ppt_opc' \
                and 'json_cart_update' not in request.session:
            # Create or Update sales Order
            # and set the Quantity to the value of the qty selector in the checkoutbox
            if 'add_qty' in kwargs and not 'set_qty' in kwargs:
                kwargs['set_qty'] = kwargs['add_qty']
            if not kwargs.get('product_id'):
                kwargs['product_id'] = product.id
            _logger.warning("product(): self.cart_update(**kwargs)")
            self.cart_update(**kwargs)

        # Remove all other products from the so if there is an individual payment acquirer config for this product
        if product.product_page_template == u'website_sale_donate.ppt_opc' and product.product_acquirer_lines_ids:
                order = request.website.sale_get_order()
                if order and order.website_order_line:
                    so_lines = order.website_order_line
                    if len(so_lines) > 1 or so_lines[0].product_id.id != product.id:
                        # TODO: Swap Sale Orders instead of cleaning products from this one
                        #       Even better would be to check if the current so works with the product acquirer config!
                        # TODO: remove all products from SO except this one!
                        for line in so_lines:
                            if line.product_id.id != product.id:
                                _logger.error("Remove sale order line %s because of individual product acquirer config"
                                              % line.id)
                                self.cart_update(product_id=line.product_id.id, add_qty=-1, set_qty=0)

        # -----------------
        # ONE PAGE CHECKOUT End
        # -----------------

        # small_cart_update by json request: Remove json_cart_update in session
        # HINT: See 'def cart_update_json' below
        if 'json_cart_update' in request.session:
            request.session.pop('json_cart_update')

        # Render the regular product page (just to run the logic behind it)
        productpage = super(website_sale_donate, self).product(product, category, search, **kwargs)

        # Render Custom Product Template based on the product_page_template field if any set
        # Add One-Page-Checkout qcontext if template is ppt_opc
        if product.product_page_template:
            productpage = request.website.render(product.product_page_template, productpage.qcontext)

        # -----------------
        # ONE PAGE CHECKOUT Start
        # -----------------
        if product.product_page_template == u'website_sale_donate.ppt_opc':
            _logger.warning("product(): self.checkout(one_page_checkout=True ...")

            # Render the checkout page
            # -------------------------------------------------
            if request.httprequest.method == 'POST':
                checkoutpage = self.checkout(one_page_checkout=True, **kwargs)
            else:
                checkoutpage = self.checkout(one_page_checkout=True)

            # INDIVIDUAL ACQUIRER CONFIG FOR THIS PRODUCT START
            # -------------------------------------------------
            if product.product_acquirer_lines_ids:
                _logger.info("One page checkout product %s (ID %s) with individual payment acquirer config!" %
                             (product.name, product.id))

                # HINT: all acquirers with "globally_hidden" set are moved to acquirers_hidden in opc_payment()
                acquirers = checkoutpage.qcontext.get('acquirers', [])
                acquirers_hidden = checkoutpage.qcontext.get('acquirers_hidden', [])
                all_acquires = acquirers + acquirers_hidden

                product_acquirers = []
                acquirer_dict = {acq.id: acq for acq in all_acquires}

                # HINT: product_acquirer_lines_ids is already correctly sorted by sequence
                for line in product.product_acquirer_lines_ids:
                    if line.acquirer_id.id in acquirer_dict:
                        product_acquirers.append(acquirer_dict[line.acquirer_id.id])
                checkoutpage.qcontext['acquirers'] = product_acquirers

            # ADD THE CHECKOUTPAGE QCONTEXT TO THE PRODUCTPAGE
            # ------------------------------------------------
            productpage.qcontext.update(checkoutpage.qcontext)
        # -----------------
        # ONE PAGE CHECKOUT End
        # -----------------

        # Add Warnings if the page is called (redirected from cart_update) with warnings in GET request
        productpage.qcontext['warnings'] = kwargs.get('warnings')
        kwargs['warnings'] = None

        # Find selected payment interval
        # 1. Set payment interval from form post data
        if kwargs.get('payment_interval_id'):
            productpage.qcontext['payment_interval_id'] = kwargs.get('payment_interval_id')
        # 2. Or Set payment interval from defaults (only if not already set in productpage.qcontext)
        if not productpage.qcontext.get('payment_interval_id'):
            payment_interval_id = self._get_payment_interval_id(product)
            if payment_interval_id:
                productpage.qcontext['payment_interval_id'] = payment_interval_id

        # Get values from existing sale-order-line for price_donate and payment_interval_id
        sale_order_id = request.session.sale_order_id
        if sale_order_id:
            # Search for a sale-order-line for the current product in the sales order of the current session
            sol_obj = request.registry['sale.order.line']
            # Get sale-order-line id if product or variant of product is in active sale order
            sol = sol_obj.search(cr, SUPERUSER_ID,
                                 [['order_id', '=', sale_order_id],
                                  ['product_id', 'in', product.ids + product.product_variant_ids.ids]],
                                 context=context)
            if len(sol) == 1:
                # Get the sale.order.line
                sol = sol_obj.browse(cr, SUPERUSER_ID, sol[0], context=context)
                if sol.exists():

                    # Add the Arbitrary Price to the qweb template context
                    if sol.price_donate:
                        productpage.qcontext['price_donate'] = sol.price_donate

                    # Add the Payment Interval to the qweb template context
                    if sol.payment_interval_id and sol.payment_interval_id in sol.product_id.payment_interval_ids:
                        productpage.qcontext['payment_interval_id'] = sol.payment_interval_id.id

        _logger.warning("product(): END")
        return productpage

    # SHOPPING CART: add keep to the values of qcontext
    # /shop/cart
    @http.route()
    def cart(self, **post):
        try:
            _logger.warning("cart(): START %s" % request.httprequest)
        except:
            _logger.warning("cart(): START")

        cartpage = super(website_sale_donate, self).cart(**post)
        cartpage.qcontext['keep'] = QueryURL(attrib=request.httprequest.args.getlist('attrib'))

        # One-Page-Checkout
        if request.website['one_page_checkout']:

            _logger.warning("cart(): END, opc redirect to /shop/checkout")
            return request.redirect("/shop/checkout")

        _logger.warning("cart(): END")
        return cartpage

    # NEW ROUTE: SIMPLE CHECKOUT:
    # Add an alternative route for products to directly add them to the shopping cart and DIRECTLY go to the checkout
    # This is useful if you want to create buttons to directly pay / donate for a product
    # HINT: We have to use product.product because otherwise we could not directly check out product variants AND
    #       _cart_update expects an product.product id anyway
    @http.route(['/shop/simplecheckout/<model("product.product"):product>',
                 '/shop/simple_checkout/<model("product.product"):product>'],
                auth="public", website=True)
    def simple_checkout(self, product, **kw):
        try:
            _logger.warning("simple_checkout(): START %s" % request.httprequest)
        except:
            _logger.warning("simple_checkout(): START")

        kw.update(simple_checkout=True)
        _logger.warning("simple_checkout(): END, return self.cart_update(product, **kw)")
        return self.cart_update(product, **kw)

    # SHOPPING CART UPDATE
    # /shop/cart/update
    # HINT: can also be called by Products-Listing Category Page if add-to-cart is enabled
    @http.route(['/shop/cart/update'])
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        try:
            _logger.warning("cart_update(): START %s" % request.httprequest)
        except:
            _logger.warning("cart_update(): START")

        cr, uid, context = request.cr, request.uid, request.context

        product = request.registry['product.product'].browse(cr, SUPERUSER_ID, int(product_id), context=context)

        # Redirect to the calling page (referrer) if the browser has added it
        # HINT: Not every browser adds the referrer to the header
        referrer = request.httprequest.referrer
        if not referrer:
            if request.session.get('last_page'):
                referrer = request.session.get('last_page')
            else:
                referrer = '/shop/product/%s' % product.product_tmpl_id.id
        if '?' not in referrer:
            referrer = referrer + '?'

        # Validate (donation) Arbitrary Price
        warnings = None
        price = kw.get('price_donate') or product.list_price or product.price
        # HINT: If price_donate is not a valid number it will be empty and so the product.list_price is used!
        #       Therefore the try statement is not really needed (but kept for safety).
        try:
            if product.price_donate_min and float(product.price_donate_min) > float(price):
                warnings = _('Value must be higher or equal to %s.' % float(product.price_donate_min))
        except ValueError:
            warnings = _('Value must be a valid Number.')
            pass
        if warnings:
            referrer = referrer + '&warnings=' + warnings
            _logger.warning("cart_update(): END, arbitrary price error")
            return request.redirect(referrer)

        # PAYMENT INTERVAL
        # INFO: This is only needed if products are directly added to cart on shop pages (product listings)
        if 'payment_interval_id' not in kw:
            payment_interval_id = self._get_payment_interval_id(product)
            if payment_interval_id:
                kw['payment_interval_id'] = payment_interval_id

        # ARBITRARY PRICE (price_donate)
        # HINT: price_donate= can already be set! See _cart_update in website_sale_donate.py

        # Call Super
        # INFO: Pass kw to _cart_update to transfer all post variables to _cart_update
        #       This is needed to get the Value of the arbitrary price from the input field
        order_line = request.website.sale_get_order(force_create=1, context=context)._cart_update(product_id=int(product_id),
                                                                                             add_qty=float(add_qty),
                                                                                             set_qty=float(set_qty),
                                                                                             context=context,
                                                                                             **kw)
        order = request.website.sale_get_order(context=context)
        _logger.warning("cart_update(): sale order number %s" % order.name)

        # FSTOKEN: Set sales order partner by fs_ptoken
        # HINT: Only use or check the token if there is an order and the user is NOT logged in!
        # TODO: should we log the token to the sale.order.line also if logged in but different partner for valid token?
        # if order and request.website.user_id.id == uid:
        #     fs_ptoken = kw.get('fs_ptoken', None)
        #     partner, messages_token, warnings_token, errors_token = fstoken(fs_ptoken=fs_ptoken)
        #     if partner:
        #         values = {'partner_id': partner.id,
        #                   'partner_invoice_id': partner.id,
        #                   'partner_shipping_id': partner.id,
        #                   }
        #         order_obj = request.registry['sale.order']
        #         order_obj.write(cr, SUPERUSER_ID, [order.id], values, context=context)
        #         # Update the sale.order.line with the fstoken for statistics
        #         if order_line and order_line.get('line_id'):
        #             order_line_obj = request.registry['sale.order.line']
        #             order_line_obj.write(cr, SUPERUSER_ID, [order_line.get('line_id')],
        #                                  {'fs_ptoken': fs_ptoken}, context=context)

        # EXIT A) Simple Checkout
        if product.simple_checkout or kw.get('simple_checkout'):
            kw.pop('simple_checkout', None)

            # Redirect to the product page if product-page-layout is one-page-checkout
            if product.product_page_template == u'website_sale_donate.ppt_opc':
                _logger.warning("cart_update(): END, EXIT A) Simple Checkout, redirect to /shop/product/... ")
                return request.redirect('/shop/product/' + str(product.product_tmpl_id.id))

            # Redirect to the checkout page
            # return request.redirect('/shop/checkout' + '?' + request.httprequest.query_string)
            _logger.warning("cart_update(): END, EXIT A) Simple Checkout, redirect to /shop/checkout")
            return request.redirect('/shop/checkout')

        # EXIT B) Stay on the current page if "Add to cart and stay on current page" is set
        if request.website['add_to_cart_stay_on_page']:
            _logger.warning("cart_update(): END, EXIT B) Stay on the current page")
            return request.redirect(referrer)

        # EXIT C) Redirect to the shopping cart
        _logger.warning("cart_update(): END, EXIT C) Redirect to the shopping cart")
        return request.redirect("/shop/cart")

    # /shop/cart/update_json
    @http.route()
    def cart_update_json(self, product_id, line_id, add_qty=None, set_qty=None, display=True):
        try:
            _logger.warning("cart_update_json(): START %s" % request.httprequest)
        except:
            _logger.warning("cart_update_json(): START")

        request.session['json_cart_update'] = 'True'
        _logger.warning("cart_update_json(): END, super(website_sale_donate, self).cart_update_json(...)")
        return super(website_sale_donate, self).cart_update_json(product_id, line_id,
                                                                 add_qty=add_qty, set_qty=set_qty, display=display)


    # Add Shipping and Billing Fields to values (= the qcontext for the checkout template)
    # HINT: The calculated values for the fields can be found in the qcontext dict in key 'checkout'
    def checkout_values(self, data=None):
        values = super(website_sale_donate, self).checkout_values(data=data)

        # Sort countries and states in values
        # -----------------------------------
        # Add sorted countries and states
        # HINT: Sort by "language in context" for name field is not implemented in o8 fixed in o9 and up!
        #       https://github.com/odoo/odoo/issues/5283
        start_locale = locale.getlocale()

        # Try to set locale by website language for correct unicode sorting by name of countries
        try:
            locale.setlocale(locale.LC_ALL, request.env.context.get("lang", "de_AT") + ".UTF-8")
        except Exception as e:
            logging.error("Could not set locale for country and state sorting by website lang!")
            pass

        # Sorted Countries (add Austria, Germany and Swiss to the top)
        # HINT: It is NO Problem if they are twice in the list :)
        countries_obj = request.env['res.country'].sudo()
        countries = countries_obj.search([])
        countries_sorted = sorted(countries, cmp=locale.strcoll, key=lambda c: c.name)
        countries_sorted_ids = [c.id for c in countries_sorted]

        swiss = countries_obj.search([('code', '=', 'CH')])
        if swiss:
            countries_sorted_ids = [swiss.id] + countries_sorted_ids

        germany = countries_obj.search([('code', '=', 'DE')])
        if germany:
            countries_sorted_ids = [germany.id] + countries_sorted_ids

        austria = countries_obj.search([('code', '=', 'AT')])
        if austria:
            countries_sorted_ids = [austria.id] + countries_sorted_ids

        countries = countries_obj.browse(countries_sorted_ids)
        # Update values
        if values.get('countries', False) and countries:
            values['countries'] = countries

        # Sorted States
        states_obj = request.env['res.country.state']
        states = states_obj.sudo().search([])
        states_sorted = sorted(states, cmp=locale.strcoll, key=lambda s: s.name)
        states = states_obj.sudo().browse([s.id for s in states_sorted])
        # Update values
        if values.get('states', False) and states:
            values['states'] = states

        # Revert to original locale
        try:
            locale.setlocale(locale.LC_ALL, start_locale)
        except Exception as e:
            logging.error("Could not revert to initial locale after country and state sorting by website lang!")
            pass

        # Add Billing Fields to values dict
        # ---------------------------------
        billing_fields = request.env['website.checkout_billing_fields']
        billing_fields = billing_fields.search([])
        values['billing_fields'] = billing_fields

        for field in billing_fields:
            f_name = field.res_partner_field_id.name
            f_type = field.res_partner_field_id.ttype
            # FIX: Set value to python True or False for all boolean fields (instead of true or false)
            if f_type == 'boolean':
                if values['checkout'].get(f_name) == 'True' or values['checkout'].get(f_name):
                    values['checkout'][f_name] = True
                else:
                    values['checkout'][f_name] = False
            # Fix for Date fields: convert '' to None
            elif f_type == 'date':
                values['checkout'][f_name] = values['checkout'].get(f_name).strip() if values['checkout'].get(f_name)\
                    else None

        # Add Shipping Fields to values dict
        # ----------------------------------
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([])
        values['shipping_fields'] = shipping_fields

        for field in shipping_fields:
            f_name = 'shipping_' + field.res_partner_field_id.name
            f_type = field.res_partner_field_id.ttype
            if f_type == 'boolean':
                if values['checkout'].get(f_name) == 'True' or values['checkout'].get(f_name):
                    values['checkout'][f_name] = True
                else:
                    values['checkout'][f_name] = False
            elif f_type == 'date':
                values['checkout'][f_name] = values['checkout'].get(f_name).strip() if values['checkout'].get(f_name) \
                    else None

        # Add option-tag attributes for shipping-address-selector for wsd_checkout_form_billing_fields template
        # -----------------------------------------------------------------------------------------------------
        if values.get('shippings'):
            shippings_selector_attrs = dict()
            # Render the dict for every shipping res.partner
            for shipping in values.get('shippings'):
                field_data = dict()
                for field in shipping_fields:
                    f_name = field.res_partner_field_id.name
                    field_data['data-shipping_' + f_name] = shipping[f_name]
                shippings_selector_attrs[shipping.id] = field_data
            values['shippings_selector_attrs'] = shippings_selector_attrs

        return values

    # Set mandatory billing and shipping fields
    def _get_mandatory_billing_fields(self):
        billing_fields = request.env['website.checkout_billing_fields']
        billing_fields = billing_fields.search([('res_partner_field_id', '!=', False),
                                                ('show', '=', True),
                                                ('mandatory', '=', True)])
        mandatory_bill = [field.res_partner_field_id.name for field in billing_fields]
        return mandatory_bill

    def _get_optional_billing_fields(self):
        billing_fields = request.env['website.checkout_billing_fields']
        billing_fields = billing_fields.search([('res_partner_field_id', '!=', False),
                                                ('show', '=', True),
                                                ('mandatory', '=', False)])
        optional_bill = [field.res_partner_field_id.name for field in billing_fields]
        return optional_bill

    def _get_mandatory_shipping_fields(self):
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([('res_partner_field_id', '!=', False),
                                                  ('show', '=', True),
                                                  ('mandatory', '=', True)])
        mandatory_ship = [field.res_partner_field_id.name for field in shipping_fields]
        return mandatory_ship

    def _get_optional_shipping_fields(self):
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([('res_partner_field_id', '!=', False),
                                                  ('show', '=', True),
                                                  ('mandatory', '=', False)])
        optional_ship = [field.res_partner_field_id.name for field in shipping_fields]
        return optional_ship

    # =================
    # ONE PAGE CHECKOUT
    # =================

    # Render the payment page with an additional dictionary acquirers_opc for One-Page-Checkout
    def opc_payment(self, **post):
        _logger.warning("opc_payment(): START")
        opc_warnings = list()

        # ---------------
        # UPDATE DELIVERY
        # ---------------
        # Update the delivery and then remove carrier_id from post to not always generate a redirection!
        # HINT: self.payment(**post) will basically just call _check_carrier_quotation() ir a carrier_id is in post
        #       and return a redirection to the payment page again.
        # ATTENTION: _check_carrier_quotation() was completely rewritten to avoid unnecessary writes to the SO!
        # HINT: with carrier id website_sale_delivery payment() would update the SO and therefore the acquierer buttons
        #       would never be rendered. this is why we need to run it twice if a carrier_id is found in post!
        # HINT: This basically runs _check_carrier_quotation() and returns a redirect to /shop/payment if carrier_id is
        #       in post!
        # TODO: check what we should do with errors at this stage
        # ATTENTION: Input names are delivery_type which is normally remapped by java script to a call to
        #            window.location.href = '/shop/payment?carrier_id=' + carrier_id;
        carrier_id = post.get('delivery_type')
        if carrier_id:
            post['carrier_id'] = int(carrier_id)
            _logger.warning("opc_payment(): 'delivery_type' = 'carrier_id' found in post (ID: %s)" % carrier_id)
            _logger.warning("opc_payment(): Run original payment() to update SO for delivery method")
            super(website_sale_donate, self).payment(**post)
            _logger.warning("opc_payment(): Pop carrier_id from post to render acquirer forms in next step")
            post.pop('carrier_id')

        # --------------------------------------------------------
        # CREATE THE PAYMENT TRANSACTION AND UPDATE THE SALE ORDER
        # --------------------------------------------------------
        # TODO: Maybe this needs to be done before UPDATE DELIVERY?
        acquirer_id = post.get('acquirer')
        if acquirer_id:
            acquirer_id = int(acquirer_id)
            _logger.warning("opc_payment(): 'acquirer' (ID: %s) found in post" % acquirer_id)
            _logger.warning("opc_payment(): add 'acquirer' to session")
            request.session['acquirer_id'] = acquirer_id
            _logger.warning("opc_payment(): CREATE THE PAYMENT TRANSACTION AND UPDATE THE SALE ORDER")
            tx = self.payment_transaction_logic(acquirer_id=acquirer_id)
            if not tx:
                _logger.error("opc_payment(): ERROR payment_transaction_logic() returned nothing! WHAT NOW?")
                opc_warnings.append(_('Please add at least one product'))

        # --------------------------------------------------
        # CALL ORIGINAL payment() TO RENDER ACQUIRER BUTTONS
        # --------------------------------------------------
        _logger.warning("opc_payment(): run super().payment(**post)")
        payment_page = super(website_sale_donate, self).payment(**post)

        # ----------------
        # CHECK FOR ERRORS
        # ----------------
        _logger.warning("opc_payment(): CHECK FOR ERRORS")
        # TODO: Check if this works with INTEGRATE LOGIC FROM PAYMENT ...
        # TODO: Check what we should do if we have a carrier id
        # Check for Errors or just redirect triggered by payment() overwrite from website_sale_delivery
        if not hasattr(payment_page, 'qcontext') or not payment_page.qcontext:
            _logger.error('opc_payment(): Orig payment page has NO QCONTEXT!')
            return payment_page
        if opc_warnings:
            payment_page.qcontext['opc_warnings'] = opc_warnings
            _logger.error('opc_payment(): opc_warnings found')
            return payment_page
        if payment_page.qcontext.get('errors'):
            _logger.error('opc_payment(): qcontext.errors found in original payment page')
            return payment_page

        # ---------------------------
        # ADD acquirer_id TO QCONTEXT
        # ---------------------------
        # HINT: This is not needed for payment() but for checkout() if OPC
        _logger.warning("opc_payment(): ADD acquirer_id TO QCONTEXT")
        if acquirer_id:
            _logger.warning('opc_payment(): add "acquirer_id" to qcontext')
            payment_page.qcontext.update({'acquirer_id': int(acquirer_id)})

        # ----------------------------------------------------------------
        # CHECK IF THERE IS ALREADY A PAYMENT TRANSACTION LINKED TO THE SO
        # ----------------------------------------------------------------
        # Odoo changed the rendering of the pay-now-button forms and only add the payment transaction reference
        # in the function payment_transaction(). This is a problem for our payment providers where we want the user
        # to add custom information like IBAN or BIC or the checkbox for the payment slips. Therefore we re-add it here
        _logger.warning("opc_payment(): CHECK IF THERE IS ALREADY A PAYMENT TRANSACTION LINKED TO THE SO")
        tx = request.website.sale_get_transaction()
        if tx:
            cr, uid, context = request.cr, request.uid, request.context
            payment_obj = request.registry.get('payment.acquirer')
            order = request.website.sale_get_order(context=context)
            # Get the order as Superuser again to gain access to all fields
            order = request.registry['sale.order'].browse(cr, SUPERUSER_ID, order.id, context=context)
            for acquirer in payment_page.qcontext['acquirers']:
                if tx.acquirer_id.id == acquirer.id:
                    # Render the acquirer button again but now with correct payment transaction reference
                    _logger.warning("opc_payment(): Render the acquirer button again but now with "
                                    "correct payment transaction reference: %s" % tx.reference)
                    acquirer.button = payment_obj.render(
                        cr, SUPERUSER_ID, acquirer.id,
                        tx.reference,
                        order.amount_total,
                        order.pricelist_id.currency_id.id,
                        partner_id=order.partner_shipping_id.id or order.partner_invoice_id.id,
                        tx_values={
                            'return_url': '/shop/payment/validate',
                        },
                        context=dict(context, submit_class='btn btn-primary', submit_txt=_('Pay Now')))

        # ---------------------------------------------------
        # ADD EXTRA INFORMATION TO QCONTEXT FOR OPC TEMPLATES
        # ---------------------------------------------------
        _logger.warning("opc_payment(): ADD EXTRA INFORMATION TO QCONTEXT FOR OPC TEMPLATES")
        payment_qcontext = payment_page.qcontext

        # ATTENTION: Always use one page checkout for the payment page
        payment_qcontext['one_page_checkout'] = True

        # Add Billing Fields to qcontext for address display
        billing_fields_obj = request.env['website.checkout_billing_fields']
        payment_qcontext['billing_fields'] = billing_fields_obj.search([])

        # Add Shipping Fields qcontext for address display
        shipping_fields_obj = request.env['website.checkout_shipping_fields']
        payment_qcontext['shipping_fields'] = shipping_fields_obj.search([])

        # Ugly hack to make getattr available in the payment page qweb templates
        payment_qcontext['getattr'] = getattr

        # ------------------------------------------------------------------------------------------------------
        # CHANGE ORIGINAL ACQUIRER BUTTON FORMS AND ADD A SECOND SET OF BUTTONS WITHOUT A FORM FOR OPC TEMPLATES
        # ------------------------------------------------------------------------------------------------------
        _logger.warning("opc_payment(): CHANGE ORIGINAL ACQUIRER BUTTON FORMS")
        for acquirer in payment_qcontext['acquirers']:

            # SET ORIGINAL INPUT TAGS TO POST DATA IF ANY
            # HINT: right now this is only useful for the iban and bic field from the pp "payment_frst"
            # HINT: "target"="_top" for iframes is already set in website_sale_donate.payment_acquirer.xml
            # HINT: The values of the input fields would only be available in **post as the prefixed names
            # HINT: We do change the content of the "value" attribute but NOT the content of the "name" attribute here!
            button = etree.fromstring(acquirer.button)
            assert button.tag == 'form', "ERROR: One Page Checkout: Payment Button has not <form> as root tag!"
            for form_input in button.iter("input"):
                if form_input.get('name'):
                    prefixed_input_name = "aq" + str(acquirer.id) + '_' + str(form_input.get('name'))
                    if not form_input.get('value') and prefixed_input_name in post:
                        form_input.set('value', post.get(prefixed_input_name))
                        # For checkboxes:
                        if form_input.get('type') == 'checkbox' and post.get(prefixed_input_name, False):
                            form_input.set('checked', 'checked')
            acquirer.button = etree.tostring(button, encoding='UTF-8', pretty_print=True)

            # CREATE A SECOND VERSION OFF THE ACQUIRER BUTTONS FOR OPC (stored in 'button_opc' instead of 'button')
            # http://lxml.de/lxmlhtml.html
            # http://lxml.de/tutorial.html
            # Changes:
            #   - Prefix the content of the "name" attribute for input tags with aq[id]_[originalname]
            #   - Set post value (The value of input fields from **post was already set above. So nothing to do here.)
            #   - Remove surrounding "form" tag
            #   - Remove submit button
            # HINT: See templates_60_checkout_steps.xml > wsd_opc_payment for details
            # HINT: We have to do it this way because any PP inherits from the template payment.acquirer_form.xml
            #       Therefore we can not just change one template but would need to modificate all templates of PP's.
            #       To avoid this we change the rendered content here after all template merging and rendering is done.
            button = etree.fromstring(acquirer.button)
            # Prefix input tag 'name' attribute value with aq[id]_[originalname]
            # HINT: This is needed because for OPC Pages all input fields of all acquirer buttons are in one form
            #       Therefore we have to make sure that all input tag names are unique
            for form_input in button.iter("input"):
                if form_input.get('name'):
                    form_input.set('name', "aq" + str(acquirer.id) + '_' + str(form_input.get('name')))
            # Remove the Pay-Now button
            # HINT: Element tree functions will return  None if an element is not found, but an empty element
            #       will have a boolean value of False because it acts like a container
            if button.find(".//button") is not None:
                button.find(".//button").getparent().remove(button.find(".//button"))

            # Store the form tag attributes in extra input fields
            # HINT: For debug only right now. Maybe we need them in them in the future e.g.: in java script
            for item in ['action', 'method', 'target']:
                child = etree.SubElement(button, "input")
                child.set('name', "aq" + str(acquirer.id) + '_form_' + item)
                child.set('type', 'hidden')
                child.set('value', button.get(item))

            # Replace the form tag with a div tag
            button_new = etree.Element('div')
            button_new.set('id', "aq" + str(acquirer.id))
            for child in button:
                button_new.append(child)
            button = button_new

            # Convert the button etree back to a string and store it in button_opc
            # print(etree.tostring(button, encoding='UTF-8', pretty_print=True))
            acquirer.button_opc = etree.tostring(button, encoding='UTF-8', pretty_print=True)

        # ---------------------------------
        # ACQUIRER SELECTION AND VALIDATION
        # ---------------------------------
        if post.get('acquirer'):
            _logger.warning("opc_payment(): ACQUIRER SELECTION AND VALIDATION")
            # Set the current acquirer to be correctly pre selected on subsequent renders of the checkout page
            payment_qcontext['acquirer_id'] = post.get('acquirer')

            # Validate if the current acquirer matches the sales order payment interval
            order = request.website.sale_get_order()
            acquirer = request.env['payment.acquirer']
            acquirer = acquirer.search([('id', '=', post.get('acquirer'))])
            if order and acquirer and (order.has_recurring and not acquirer.recurring_transactions):
                msg = _('The selected payment method does not support recurring payments!')
                _logger.warning(msg)
                # HINT that the qcontext has no errors is checked above already
                payment_qcontext['errors'] = {'pm_recurring': [_('Wrong payment method'), msg]}

            # TODO: Validate acquirer input fields e.g.: iban and bic
            #       Maybe add a new method to payment providers: e.g.: _[paymentmethod]_pre_send_form_validate()

        # --------------------------------------
        # ADD "acquirer_auto_submit" TO QCONTEXT
        # --------------------------------------
        acquirer_active = False
        if acquirer_id:
            _logger.warning("opc_payment(): ADD 'acquirer_auto_submit' TO QCONTEXT")
            for acquirer in payment_qcontext['acquirers']:
                if int(acquirer.id) == acquirer_id:
                    acquirer_active = acquirer
                    break
            if not acquirer_active:
                _logger.error('opc_payment(): ERROR selected acquirer not found in acquirers!')
                if not payment_qcontext.get('opc_warnings'):
                    payment_qcontext['opc_warnings'] = list()
                payment_qcontext['opc_warnings'].append(_('Please select an other acquirer.'))
            payment_qcontext['acquirer_auto_submit'] = acquirer_active

        # -------------------------------------------------------
        # MOVE ACQUIRERS WITH globally_hidden TO acquirers_hidden
        # -------------------------------------------------------
        _logger.warning("opc_payment(): MOVE ACQUIRERS WITH globally_hidden TO acquirers_hidden")
        # HINT: This is for individual payment acquirer configuration per one page checkout product
        # https://stackoverflow.com/questions/1207406/remove-items-from-a-list-while-iterating
        payment_qcontext['acquirers_hidden'] = [acq for acq in payment_qcontext['acquirers'] if acq.globally_hidden]
        payment_qcontext['acquirers'][:] = [acq for acq in payment_qcontext['acquirers'] if not acq.globally_hidden]

        _logger.warning("opc_payment(): END")
        # TODO: Remove the parts added here from checkout() and payment()
        return payment_page

    # payment_transaction controller method (json route) gets replaced with this method
    # (see below for /shop/payment/transaction/<int:acquirer_id> and in checkout controller for one-page-checkout)
    # This is called either by the json route after the pay-now button is pressed or during the one-page-checkout
    # HINT: We can not directly call payment_transaction e.g.:
    def payment_transaction_logic(self, acquirer_id, checkout_page=None, **post):
        _logger.warning("payment_transaction_logic(): START")

        # TODO: CREATE totally new logic how we deal with cancelations on and returns from the PP
        # To make sure we have not problem we should:
        # duplicate the SO (so it is without related tx) so we have a new one for later
        # - Create a new TX with the SO Number as the reference
        # - Update the Sale Order
        #   - Add the newly created draft tx and the related acquirer (payment_acquirer_id, payment_tx_id)
        #   - Set the sale order to state "send" (= No further changes possible except by an pp answer)
        # - Activate the duplicated SO in the current session so if there is a return from the pp without an pp answer
        #   one could even change the SO and retry it again so he has a new SO and will generate a new TX if he submits
        #   it again to the PP - which is ideal ;) - we could even store this in the session and delete the duplicate
        #   if there are no changes compared to the original so in "sent" state in the form feedback when we process the
        #   Answer from the pp

        # TODO: Use the same behaviour for the regular payment page!
        #       (use opc_buttons and just one submit button and submit to /payment again - no java script needed!)
        # ATTENTION: Don't forget to change the original payment page template to use the special buttons and
        #            only one submit button just like for any opc page - so it is more or less the same behaviour.
        #            The only drawback is that also on the payment page it will submitt its data to itself instead
        #            direclty submitting it to the pp BUT because of this we will get any additional from info
        #            of non hidden fields like IBAN, BIC or not payment forms needed for fsotransfer

        # TODO: Remove the call to the original controller after the stuff from above is done!
        # ATTENTION: This call to the json controller may destroy the session: Carefully test this !!!
        # HINT: If there was no order or no order-line or no acquirer_id "pt" would be a redirect to "/shop/checkout"
        _logger.info("payment_transaction_logic(): call original payment_transaction()")
        pt = super(website_sale_donate, self).payment_transaction(acquirer_id=int(acquirer_id))

        # TODO: 'return_url': '/shop/payment/validate', check if this prevents our custom return urls!
        return pt

    # /shop/payment/transaction/<int:acquirer_id>
    # Overwrite the Json controller for the pay now button
    @http.route()
    def payment_transaction(self, acquirer_id, **post):
        _logger.warning("payment_transaction(): START post data: \n%s\n" % post or None)
        _logger.info(_('Call of json route /shop/payment/transaction/%s will start payment_transaction_logic()')
                     % acquirer_id)
        # HINT: payment_transaction_logic() will only run the original payment_transaction().
        #       This is only done so "akward" not to kill the session if the checkout page needs to call this logic
        #       on the server instead of the browser of the user calling it. With this trick the call to
        #       payment_transaction_logic() inside of checkout (see step 3) will not create a new session.
        pay_now_button_form = self.payment_transaction_logic(acquirer_id)
        return pay_now_button_form

    # Checkout Page
    @http.route()
    def checkout(self, one_page_checkout=False, **post):
        try:
            _logger.warning("checkout(): START %s" % request.httprequest)
        except:
            _logger.warning("checkout(): START")

        cr, uid, context = request.cr, request.uid, request.context

        # Render the Checkout Page
        checkout_page = super(website_sale_donate, self).checkout(**post)
        if not hasattr(checkout_page, 'qcontext'):
            _logger.warning("checkout(): END, checkout_page has no qcontext. Most likely a redirection after error!")
            return checkout_page

        # Add the acquirer id to the checkoutpage qcontext
        if post and post.get('acquirer'):
            checkout_page.qcontext.update({'acquirer_id': post.get('acquirer')})

        # -----------------------
        # NOT A ONE PAGE CHECKOUT
        # -----------------------
        if not (request.website['one_page_checkout'] or one_page_checkout):
            _logger.warning("checkout(): END")
            return checkout_page

        # -----------------
        # ONE PAGE CHECKOUT
        # -----------------
        _logger.warning("checkout(): One-Page-Checkout is enabled and checkout_page is not just a redirection")

        # Make sure one one_page_checkout is true and in the qcontext
        checkout_page.qcontext['one_page_checkout'] = True

        # Checkout-Page was called for the first time
        # -------------------------------------------
        if request.httprequest.method != 'POST':
            payment_page = self.opc_payment()
            checkout_page.qcontext.update(payment_page.qcontext)
            _logger.warning("checkout(): END, GET request (without post data)")
            return checkout_page

        # Checkout-Page was already called and now submits it's form data
        # ---------------------------------------------------------------
        if request.httprequest.method == 'POST':

            # STEP 1: UPDATE DELIVERY
            # HINT: self.payment(**post) will basically just call _check_carrier_quotation() ir a carrier_id is in post
            #       and return a redirection to the payment page again.
            # ATTENTION: _check_carrier_quotation() was completely rewritten to avoid unnecessary writes to the SO!
            # ATTENTION: Input names are delivery_type which is normally remapped by java script to a call to
            #            window.location.href = '/shop/payment?carrier_id=' + carrier_id;
            # TODO: Test if we should directly call _check_carrier_quotation() instead of self.payment(**post)
            _logger.warning("checkout(): OPC STEP 1: UPDATE DELIVERY")
            carrier_id = post.get('delivery_type')
            if carrier_id:
                post['carrier_id'] = int(carrier_id)
                super(website_sale_donate, self).payment(**post)
                # ATTENTION: carrier_id must be removed or payment() will always return the redirection to /shop/payment
                post.pop('carrier_id')

            # STEP 2: CONFIRM ORDER
            # - Check if a sale order exists
            # - run checkout_redirection()
            # - run checkout_values()
            # - run checkout_form_validate()
            # - run checkout_form_save()
            # - run sale_get_order(update_pricelist=True)
            # HINT: Will not change the sale order state
            # HINT: Will return render("website_sale.checkout", values) if any errors are found
            #       Else it will return a redirection
            _logger.warning("checkout(): OPC STEP 2: RUN CONFIRM ORDER")
            confirm_order = self.confirm_order(**post)

            # STEP 3: RUN THE ORIGINAL CHECKOUT CONTROLLER AGAIN TO HONOR POSSIBLE CHANGES BY DELIVERY
            # - run sale_get_order(force_create=1)
            # - run checkout_redirection()
            # - run checkout_values()
            # - render("website_sale.checkout", values)
            _logger.warning("checkout(): OPC STEP 3: RUN THE ORIGINAL CHECKOUT CONTROLLER AGAIN")
            checkout_page = super(website_sale_donate, self).checkout(**post)
            # ATTENTION: Always use one page checkout for the checkout_page
            checkout_page.qcontext['one_page_checkout'] = True
            # Add opc_warnings used in opc templates to display errors
            checkout_page.qcontext['opc_warnings'] = list()
            # Add errors from confirm_order if any
            # ATTENTION: If confirm_order has a qcontext it means checkout_form_validate() returned errors
            # ATTENTION: Errors in confirm_order may shadow errors in the checkoutpage therefore we add it to
            #            opc_warnings before we add the qcontext to the checkoutpage
            if hasattr(confirm_order, 'qcontext'):
                checkout_page.qcontext['opc_warnings'].append(confirm_order.qcontext.get('errors', []))
                checkout_page.qcontext.update(confirm_order.qcontext)

            # STEP 4: RENDER THE PAYMENT BUTTONS (Forms)
            _logger.warning("checkout(): OPC STEP 4: RENDER THE PAYMENT BUTTONS (opc_payment())")
            payment_page = self.opc_payment(**post)
            # ATTENTION: Errors in the payment page may shadow errors in the checkoutpage therefore we add it to
            #            opc_warnings before we add the qcontext to the checkoutpage
            if payment_page.qcontext.get('errors'):
                checkout_page.qcontext['opc_warnings'].append(payment_page.qcontext.get('errors', []))
            # Add the payment page qcontext to the checkoutpage qcontext
            checkout_page.qcontext.update(payment_page.qcontext)

            # STEP 5: CHECK FOR ERRORS
            # HINT: We redirect so late to make sure qcontext of the payment page is already in the checkoutpage
            #       because it is needed in OPC templates.
            # ATTENTION: If confirm_order has a qcontext it means checkout_form_validate() returned errors
            # ATTENTION: Errors in the qcontext for confirm order may shadow errors from the payment- and checkoutpage
            _logger.warning("checkout(): OPC STEP 5: CHECK FOR ERRORS")
            if checkout_page.qcontext.get('error') or confirm_order.location != '/shop/payment':
                _logger.warning("checkout(): ERRORS FOUND RETURNING CHECKOUTPAGE")
                return checkout_page

            _logger.warning("checkout(): SUCCESS! RETURNING CHECKOUTPAGE WITH 'acquirer_auto_submit' FOR PP REDIRECT!")
            return checkout_page

    # One-Page-Checkout: Payment Page Redirection
    # HINT: Shopping Cart Redirection is done above around line 92
    @http.route()
    def payment(self, **post):
        try:
            _logger.warning("payment(): START %s" % request.httprequest)
        except:
            _logger.warning("payment(): START")

        # OPC enabled for the whole website = redirect to checkout page
        # HINT: If one_page_checkout is enabled globally for the webshop the payment page is not
        #       used because the payment templates are displayed already on the checkout page (= shop OPC)
        if request.website['one_page_checkout']:
            _logger.warning("payment(): END, opc in session therefore redirect to /shop/checkout")
            return request.redirect("/shop/checkout")

        _logger.warning("payment(): END: RETURN self.opc_payment(**post)")
        return self.opc_payment(**post)

    # Override of /shop/payment/validate
    # ATTENTION: All payment providers will redirect after its [name]_form_feedback() to /shop/payment/validate
    # HINT: Overwrite was necessary because of unwanted redirects e.g.: to /shop in orig. controller
    @http.route()
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        sale_order_obj = request.registry['sale.order']

        # Redirect URL
        # TODO: check if last_shop_page and last_page is really a good idea or if /shop/confirmation_static is enough
        redirect_url_after_form_feedback = (request.registry.get('last_shop_page') or
                                            request.registry.get('last_page') or '/shop/confirmation_static')

        # Update redirect_url_after_form_feedback from global website setting
        if request.website and request.website.redirect_url_after_form_feedback:
            redirect_url_after_form_feedback = request.website.redirect_url_after_form_feedback

        # Find payment transaction (from current session)
        if transaction_id is None:
            tx = request.website.sale_get_transaction()
        else:
            tx = request.registry['payment.transaction'].browse(cr, uid, transaction_id, context=context)

        # Update redirect_url_after_form_feedback from payment provider if set
        if tx and tx.acquirer_id and tx.acquirer_id.redirect_url_after_form_feedback:
            # From Payment Provider
            redirect_url_after_form_feedback = tx.acquirer_id.redirect_url_after_form_feedback

        # Update redirect_url_after_form_feedback from sale-order-root_cat
        if tx and tx.sale_order_id \
                and tx.sale_order_id.cat_root_id \
                and tx.sale_order_id.cat_root_id.redirect_url_after_form_feedback:
            redirect_url_after_form_feedback = tx.sale_order_id.cat_root_id.redirect_url_after_form_feedback

        # Find sale order (from current session)
        if sale_order_id is None:
            order = request.website.sale_get_order(context=context)
        else:
            order = request.registry['sale.order'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
            assert order.id == request.session.get('sale_last_order_id')

        # EXIT if no sale order can be found
        if not order:
            return request.redirect(redirect_url_after_form_feedback)

        # Confirm free sale orders or cancel sale_orders
        # HINT: No payment transaction BUT a sale order with 0 total amount
        if not order.amount_total and (not tx or tx and tx.state in ['pending', 'done']):
            # Orders are confirmed by payment transactions, but there is none for free orders,
            # (e.g. free events), so confirm immediately
            order.action_button_confirm()
            # TODO: Send e-mail like in addons-own/website_sale_donate/models/payment_transaction.py
        # HINT: This may be redundant because sale order will normally already cancelled in form_feedback()
        elif tx and tx.state == 'cancel' and order.state != 'cancel':
            sale_order_obj.action_cancel(cr, SUPERUSER_ID, [order.id], context=request.context)

        # CLEAN CURRENT SESSION
        request.website.sale_reset(context=context)

        # Redirect
        divider = '?' if '?' not in redirect_url_after_form_feedback else '&'
        return request.redirect(redirect_url_after_form_feedback+divider+'order_id='+str(order.id))

    # Alternative confirmation page for Dadi Payment-Providers (Acquirers ogonedadi and frst for now)
    # HINT this rout is called by the payment_provider routes e.g.: ogonedadi_form_feedback or frst_form_feedback
    @http.route(['/shop/confirmation_static'], type='http', auth="public", website=True)
    def payment_confirmation_static(self, order_id=None, **post):
        _logger.warning("payment_confirmation_static(): START")

        cr, uid, context = request.cr, request.uid, request.context
        try:
            order_id = int(order_id)
            order = request.registry['sale.order'].browse(cr, SUPERUSER_ID, order_id, context=context)[0]
            if order and order.name and order.payment_tx_id:
                return request.website.render("website_sale_donate.confirmation_static", {'order': order})
            else:
                raise ValueError
        except:
            return request.website.render("website_sale_donate.confirmation_static", {'order': None})

    # For (small) cart JSON updates use arbitrary price (price_donate) if set sale.order.line
    @http.route()
    def get_unit_price(self, product_ids, add_qty, use_order_pricelist=False, **kw):
        product_prices = super(website_sale_donate,
                               self).get_unit_price(product_ids, add_qty, use_order_pricelist, **kw)
        # Get current Sales Order Lines for arbitrary price
        order = request.website.sale_get_order()
        if order and order.order_line:
            order_line_prices = {line.product_id.id: line.price_donate
                                 for line in order.order_line
                                 if line.product_id.price_donate}
            product_prices.update(order_line_prices)
        # Cycle through products and return arbitrary price if set
        return product_prices

    # Extra Route for Sales Order Information
    @http.route('/shop/order/get_data/<int:sale_order_id>', type='json', auth="user", website=True)
    def order_get_status(self, sale_order_id, **post):
        #cr, uid, context = request.cr, request.uid, request.context

        try:
            #order = request.env['sale.order'].sudo().search([('id', '=', sale_order_id)])
            order = request.env['sale.order'].search([('id', '=', sale_order_id)])
            assert order.ensure_one(), 'Multiple Sales Order Found!'
        except:
            order = False

        if not order:
            return {
                'error': 'None or multiple Sale Order found for the given id: %s' % sale_order_id,
            }

        try:
            data = {
                'id': order.id,
                'name': order.name,
                'state': order.state,
                'amount_total': order.amount_total,
                'order_lines': dict(),
            }
            if order.partner_id:
                data.update(partner_id={
                    'id': order.partner_id.id,
                    'name': order.partner_id.name,
                    #
                    'firstname': order.partner_id.firstname if hasattr(order.partner_id, 'firstname') else '',
                    'lastname': order.partner_id.lastname if hasattr(order.partner_id, 'lastname') else '',
                    'donation_deduction_optout_web': order.partner_id.donation_deduction_optout_web if hasattr(
                        order.partner_id, 'donation_deduction_optout_web') else '',
                    'gender': order.partner_id.gender if hasattr(order.partner_id, 'gender') else '',
                    #
                    'company_name_web': order.partner_id.company_name_web,
                    'email': order.partner_id.email,
                    'newsletter_web': order.partner_id.newsletter_web,
                    'donation_receipt_web': order.partner_id.donation_receipt_web,
                    'opt_out': order.partner_id.opt_out,
                    'lang': order.partner_id.lang,
                })
            if order.partner_invoice_id:
                data.update(partner_invoice_id={
                    'id': order.partner_invoice_id.id,
                    'name': order.partner_invoice_id.name,
                    #
                    'firstname': order.partner_invoice_id.firstname if hasattr(order.partner_invoice_id,
                                                                               'firstname') else '',
                    'lastname': order.partner_invoice_id.lastname if hasattr(order.partner_invoice_id,
                                                                             'lastname') else '',
                    'donation_deduction_optout_web': order.partner_invoice_id.donation_deduction_optout_web if hasattr(
                        order.partner_invoice_id, 'donation_deduction_optout_web') else '',
                    'gender': order.partner_invoice_id.gender if hasattr(order.partner_invoice_id, 'gender') else '',
                    #
                    'company_name_web': order.partner_invoice_id.company_name_web,
                    'email': order.partner_invoice_id.email,
                    'newsletter_web': order.partner_invoice_id.newsletter_web,
                    'donation_receipt_web': order.partner_invoice_id.donation_receipt_web,
                    'opt_out': order.partner_invoice_id.opt_out,
                    'lang': order.partner_invoice_id.lang,
                })
            if order.partner_shipping_id:
                data.update(partner_shipping_id={
                    'id': order.partner_shipping_id.id,
                    'name': order.partner_shipping_id.name,
                    #
                    'firstname': order.partner_shipping_id.firstname if hasattr(order.partner_shipping_id,
                                                                                'firstname') else '',
                    'lastname': order.partner_shipping_id.lastname if hasattr(order.partner_shipping_id,
                                                                              'lastname') else '',
                    'donation_deduction_optout_web': order.partner_invoice_id.donation_deduction_optout_web if hasattr(
                        order.partner_shipping_id, 'donation_deduction_optout_web') else '',
                    'gender': order.partner_shipping_id.gender if hasattr(order.partner_shipping_id, 'gender') else '',
                    #
                    'company_name_web': order.partner_shipping_id.company_name_web,
                    'email': order.partner_shipping_id.email,
                    'newsletter_web': order.partner_shipping_id.newsletter_web,
                    'donation_receipt_web': order.partner_shipping_id.donation_receipt_web,
                    'opt_out': order.partner_shipping_id.opt_out,
                    'lang': order.partner_shipping_id.lang,
                })
            for line in order.order_line:
                data['order_lines']['line_'+str(line.id)] = {
                    'id': line.id,
                    'name': line.name,
                    'price_subtotal': line.price_subtotal,
                    'price_unit': line.price_unit,
                    'price_donate': line.price_donate,
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'cat_root_id': line.cat_root_id.id if line.cat_root_id else 'None',
                    'cat_root_id_name': line.cat_root_id.name if line.cat_root_id else 'None',
                    'cat_id': line.cat_id.id if line.cat_id else 'None',
                    'cat_id_name': line.cat_id.name if line.cat_id else 'None',
                }
            return data
        except:
            return {
                'error': 'Could not get Data for Sale-Order %s. Maybe you have the wrong user rights?' % sale_order_id,
            }
