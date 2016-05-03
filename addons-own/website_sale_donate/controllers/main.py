# -*- coding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from lxml import etree
from urlparse import urlparse
from openerp.addons.website.models.website import slug

# import copy
# import requests

# To get a new db connection:
# from openerp.modules.registry import RegistryManager

# import the base controller class to inherit from
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.addons.website_sale.controllers.main import QueryURL

_logger = logging.getLogger(__name__)


class website_sale_donate(website_sale):

    # SHOP PAGE: Add last_shop_page to the session
    @http.route()
    def shop(self, page=0, category=None, search='', **post):
        base_url = str(urlparse(request.httprequest.base_url).path)
        request.session['last_shop_page'] = base_url + ('?category='+str(category.id) if category else '')
        request.session['last_page'] = request.session['last_shop_page']
        return super(website_sale_donate, self).shop(page=page, category=category, search=search, **post)

    # PRODUCT PAGE: Extend the product page render request to include price_donate and payment_interval
    # so we have the same settings for arbitrary price and payment interval as already set by the user in the so line
    # Todo: Would need to update the Java Script of Website_sale to select the correct product variante if it
    #       is already in the current sales order (like i do it for price_donate and payment_interval)
    #       ALSO i need to update the java script that loads the product variant pictures
    # /shop/product/<model("product.template"):product>
    @http.route()
    def product(self, product, category='', search='', **kwargs):

        # Store the current request url in the session for possible returns
        # INFO: html escaping is done by request.redirect so not needed here!
        query = {'category': category, 'search': search}
        query = '&'.join("%s=%s" % (key, val) for (key, val) in query.iteritems() if val)
        request.session['last_page'] = request.httprequest.base_url + '?' + query

        cr, uid, context = request.cr, request.uid, request.context

        # One-Page-Checkout: call cart_update
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
            self.cart_update(**kwargs)

        # small_cart_update by json request: Remove json_cart_update in session
        # HINT: See 'def cart_update_json' below
        if 'json_cart_update' in request.session:
            request.session.pop('json_cart_update')

        # Render the regular product page
        productpage = super(website_sale_donate, self).product(product, category, search, **kwargs)

        # Render Custom Product Template based on the product_page_template field if any set
        # Add One-Page-Checkout qcontext if template is ppt_opc
        if product.product_page_template:
            productpage = request.website.render(product.product_page_template, productpage.qcontext)

        # One-Page-Checkout: Only if the template is ppt_opc
        if product.product_page_template == u'website_sale_donate.ppt_opc':
            if request.httprequest.method == 'POST':
                checkoutpage = self.checkout(one_page_checkout=True, **kwargs)
            else:
                checkoutpage = self.checkout(one_page_checkout=True)
            # One-Page-Checkout Qcontext
            productpage.qcontext.update(checkoutpage.qcontext)

        # Add Warnings if the page is called (redirected from cart_update) with warnings in GET request
        productpage.qcontext['warnings'] = kwargs.get('warnings')
        kwargs['warnings'] = None

        # Find and Set default payment interval
        # 1. Set from post
        if kwargs.get('payment_interval_id'):
            productpage.qcontext['payment_interval_id'] = kwargs.get('payment_interval_id')
        # 2. Set from defaults
        if not productpage.qcontext.get('payment_interval_id'):
            if request.website.payment_interval_default:
                productpage.qcontext['payment_interval_id'] = request.website.payment_interval_default.id
            if product.payment_interval_default:
                productpage.qcontext['payment_interval_id'] = product.payment_interval_default.id
        # 3. Use first entry
        if not productpage.qcontext.get('payment_interval_id'):
            # Deprecated: payment_interval_ids
            if product.payment_interval_ids:
                productpage.qcontext['payment_interval_id'] = product.payment_interval_ids[0].id
            if product.payment_interval_lines_ids:
                productpage.qcontext['payment_interval_id'] = product.payment_interval_lines_ids[0].payment_interval_id.id

        # Get values from sale-order-line for price_donate and payment_interval_id
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

        return productpage

    # SHOPPING CART: add keep to the values of qcontext
    # /shop/cart
    @http.route()
    def cart(self, **post):

        cartpage = super(website_sale_donate, self).cart(**post)
        cartpage.qcontext['keep'] = QueryURL(attrib=request.httprequest.args.getlist('attrib'))

        # One-Page-Checkout
        if request.website['one_page_checkout']:
            return request.redirect("/shop/checkout")

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
        kw.update(simple_checkout=True)
        return self.cart_update(product, **kw)

    # SHOPPING CART UPDATE
    # /shop/cart/update
    # HINT: can also be called by Products-Listing Category Page if add-to-cart is enabled
    @http.route(['/shop/cart/update'])
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
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
            return request.redirect(referrer)

        # Check Payment Interval
        # TODO add a default payment interval to the website and per product and set this here correctly
        # INFO: This is only needed if products are directly added to cart on shop pages (product listings)
        if 'payment_interval_id' not in kw:
            if product.payment_interval_ids:
                kw['payment_interval_id'] = product.payment_interval_ids[0].id

        # Call Super
        # INFO: Pass kw to _cart_update to transfer all post variables to _cart_update
        #       This is needed to get the Value of the arbitrary price from the input field
        request.website.sale_get_order(force_create=1, context=context)._cart_update(product_id=int(product_id),
                                                                                     add_qty=float(add_qty),
                                                                                     set_qty=float(set_qty),
                                                                                     context=context,
                                                                                     **kw)

        # If simple_checkout is set for the product redirect directly to checkout or confirm_order
        if product.simple_checkout or kw.get('simple_checkout'):
            kw.pop('simple_checkout', None)
            # This will redirect directly to the payment if confirm_order finds no errors
            if kw.get('email') and kw.get('name') and kw.get('shipping_id'):
                return request.redirect('/shop/confirm_order' + '?' + request.httprequest.query_string)
            return request.redirect('/shop/checkout' + '?' + request.httprequest.query_string)

        # Stay on the current page if "Add to cart and stay on current page" is set
        if request.website['add_to_cart_stay_on_page']:
            return request.redirect(referrer)

        # Redirect to the shopping cart
        return request.redirect("/shop/cart")

    # /shop/cart/update_json
    @http.route()
    def cart_update_json(self, product_id, line_id, add_qty=None, set_qty=None, display=True):
        request.session['json_cart_update'] = 'True'
        return super(website_sale_donate, self).cart_update_json(product_id, line_id,
                                                                 add_qty=add_qty, set_qty=set_qty, display=display)


    # Add Shipping and Billing Fields to values (= the qcontext for the checkout template)
    # HINT: The calculated values for the fields can be found in the qcontext dict in key 'checkout'
    def checkout_values(self, data=None):
        values = super(website_sale_donate, self).checkout_values(data=data)

        # Add Billing Fields to values dict
        billing_fields = request.env['website.checkout_billing_fields']
        billing_fields = billing_fields.search([])
        values['billing_fields'] = billing_fields

        # Add Shipping Fields to values dict
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([])
        values['shipping_fields'] = shipping_fields

        # Set value to True or False for all boolean fields
        for field in billing_fields:
            f_name = field.res_partner_field_id.name
            if field.res_partner_field_id.ttype == 'boolean':
                if values['checkout'].get(f_name) == 'True' or values['checkout'].get(f_name):
                    values['checkout'][f_name] = True
                else:
                    values['checkout'][f_name] = False
        for field in shipping_fields:
            f_name = 'shipping_' + field.res_partner_field_id.name
            if field.res_partner_field_id.ttype == 'boolean':
                if values['checkout'].get(f_name) == 'True' or values['checkout'].get(f_name):
                    values['checkout'][f_name] = True
                else:
                    values['checkout'][f_name] = False

        # Add option-tag attributes for shipping-address-selector for wsd_checkout_form_billing_fields template
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
        billing_fields = billing_fields.search([])
        mandatory_bill = []
        for field in billing_fields:
            if field.mandatory:
                mandatory_bill.append(field.res_partner_field_id.name)
        #print "mandatory_bill %s" % mandatory_bill
        return mandatory_bill

    def _get_optional_billing_fields(self):
        billing_fields = request.env['website.checkout_billing_fields']
        billing_fields = billing_fields.search([])
        optional_bill = []
        for field in billing_fields:
            if not field.mandatory:
                optional_bill.append(field.res_partner_field_id.name)
        #print "optional_bill %s" % optional_bill
        return optional_bill

    def _get_mandatory_shipping_fields(self):
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([])
        mandatory_ship = []
        for field in shipping_fields:
            if field.mandatory:
                mandatory_ship.append(field.res_partner_field_id.name)
        #print "mandatory_ship %s" % mandatory_ship
        return mandatory_ship

    def _get_optional_shipping_fields(self):
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([])
        optional_ship = []
        for field in shipping_fields:
            if not field.mandatory:
                optional_ship.append(field.res_partner_field_id.name)
        #print "optional_ship %s" % optional_ship
        return optional_ship

    # =================
    # ONE PAGE CHECKOUT
    # =================

    # Render the payment page with an additional dictionary acquirers_opc for One-Page-Checkout
    def opc_payment(self, **post):

        # Render the payment page and therefore get all Pay-Now Button forms
        payment_page = super(website_sale_donate, self).payment(**post)
        payment_qcontext = None
        if hasattr(payment_page, 'qcontext'):
            payment_qcontext = payment_page.qcontext

        # Check for redirection caused by errors
        if not payment_qcontext:
            _logger.error(_('Payment Page has no qcontext. It may be a redirection. No Acquirer-Buttons rendered!'))
            return payment_page

        # Check for errors in qcontext
        # HINT: If errors are present Pay-Now button forms will NOT! be rendered by payment controller
        if payment_qcontext.get('errors'):
            _logger.warning(_('Errors found on the payment page! No Acquirer-Buttons rendered!'))
            return payment_page

        # Create alternative Pay-Now buttons (button_opc)
        # Remove the form and submit button, uniquely prefix the acquirer input fields and set data from post
        for acquirer in payment_qcontext['acquirers']:

            # UPDATE THE ORIGINAL PAY-NOW ACQUIRER.BUTTON FORM:
            # set input-tags value to post-data-value
            # and use target _top for aswidget
            button = etree.fromstring(acquirer.button)
            assert button.tag == 'form', "ERROR: One Page Checkout: Payment Button has not <form> as root tag!"

            # Set input-tags value to post-data value if any (e.g.: payment_frst iban- and bic-field)
            for form_input in button.iter("input"):
                if form_input.get('name'):
                    # Create button_opc field name (see code below for button_opc)
                    prefixed_input_name = "aq" + str(acquirer.id) + '_' + str(form_input.get('name'))
                    # Set value from post data if field has currently no value
                    if not form_input.get('value') and prefixed_input_name in post:
                        form_input.set('value', post.get(prefixed_input_name))

            # Use target _top if aswidget is set in session
            if request.session.get('aswidget'):
                # HINT: Button is a form see assert button.tag above
                button.set('target', '_top')

            # Store the processed xml
            acquirer.button = etree.tostring(button, encoding='UTF-8', pretty_print=True)

            # CREATE button_opc: CONVERT THE PAY-NOW BUTTON FORMS INTO INPUT FIELDS WITHOUT SURROUNDING FORM TAG:
            # to insert them into the regular checkout form
            # http://lxml.de/lxmlhtml.html
            # http://lxml.de/tutorial.html
            # Process the One-Page-Checkout version of the Pay-Now Button (=no form and submit-button but just inputs)
            button = etree.fromstring(acquirer.button)

            # Prefix the name attribute of the input tags
            for form_input in button.iter("input"):
                if form_input.get('name'):
                    # ATTENTION: Must be the same than above
                    form_input.set('name', "aq" + str(acquirer.id) + '_' + str(form_input.get('name')))

            # Remove the Pay-Now button
            # HINT: element tree functions will return  None if an element is not found, but an empty element
            #       will have a boolean value of False because it acts like a container
            if button.find(".//button") is not None:
                button.find(".//button").getparent().remove(button.find(".//button"))

            # Store the form tag attributes in extra input fields (which is not used right now but nice to have)
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

        # Acquirer Validation
        if post.get('acquirer'):

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

            # TODO: Validate acquirer non-hidden input fields
            # TODO: Validate acquirer non-hidden input fields
            # TODO: Should add a new mehtod to payment providers: e.g.: _[paymentmethod]_pre_send_form_validate()

        return payment_page

    # payment_transaction controller method (json route) gets replaced with this method
    # (see below for /shop/payment/transaction/<int:acquirer_id> and in checkout controller for one-page-checkout)
    # This is called either by the json route after the pay-now button is pressed or during the one-page-checkout
    # HINT: We do not directly overwrite the Json route because calling a json route will kill/replace current session
    def payment_transaction_logic(self, acquirer_id, checkout_page=None, **post):

        cr, uid, context = request.cr, request.uid, request.context
        transaction_obj = request.registry.get('payment.transaction')
        order = request.website.sale_get_order(context=context)

        if not order or not order.order_line or acquirer_id is None:
            _logger.error(_('Sale Order is missing or it contains no products!'))
            if checkout_page:
                if 'opc_warnings' not in checkout_page.qcontext:
                    checkout_page.qcontext['opc_warnings'] = list()
                checkout_page.qcontext['opc_warnings'].append(_('Please add products or donations.'))
                return checkout_page
            else:
                return request.redirect("/shop/checkout")

        assert order.partner_id.id != request.website.partner_id.id

        # Find an already existing transaction or create a new one
        # TODO: Transaction is not updated after first creation! We should do a force update here.
        tx = request.website.sale_get_transaction()
        if tx:
            tx_id = tx.id
            if tx.reference != order.name:
                tx = False
                tx_id = False
            elif tx.state == 'draft':  # button clicked but no more info -> rewrite on tx or create a new one ?
                tx.write({
                    'acquirer_id': acquirer_id,
                    'amount': order.amount_total,
                })
        if not tx:
            tx_id = transaction_obj.create(cr, SUPERUSER_ID, {
                'acquirer_id': acquirer_id,
                'type': 'form',
                'amount': order.amount_total,
                'currency_id': order.pricelist_id.currency_id.id,
                'partner_id': order.partner_id.id,
                'partner_country_id': order.partner_id.country_id.id,
                'reference': order.name,
                'sale_order_id': order.id,
            }, context=context)
            request.session['sale_transaction_id'] = tx_id

        # Update sale order
        so_tx = request.registry['sale.order'].write(
                cr, SUPERUSER_ID, [order.id], {
                    'payment_acquirer_id': acquirer_id,
                    'payment_tx_id': request.session['sale_transaction_id']
                }, context=context)
        if not so_tx:
            _logger.error(_('Could not update sale order after creation or update of the payment transaction!'))

        # Reset sales order of current session for Dadi Payment Providers
        # HINT: THis is the integration of the former addon website_sale_payment_fix
        # HINT: Since we have a transaction right now we reset the sale-order of the current session
        #       for our own payment providers. Therefore it does not matter what happens by the PP
        if tx_id:
            # get the payment.transaction
            tx = request.registry['payment.transaction'].browse(cr, SUPERUSER_ID,
                                                                [tx_id], context=context)

            # Only reset the current shop session for our own payment providers
            if tx.acquirer_id.provider in ('ogonedadi', 'frst', 'postfinance'):
                # Confirm the sales order so no changes are allowed any more in the odoo backend
                request.registry['sale.order'].action_button_confirm(cr, SUPERUSER_ID,
                                                                     [tx.sale_order_id.id], context=context)
                # Clear the session to restart SO in case we get no answer from the PP or browser back button is used
                request.website.sale_reset(context=context)
                # HINT: Maybe it is also needed to reset the sale_last_order_id? Disabled for now
                # request.session.update({'sale_last_order_id': False})

        return tx_id

    # /shop/payment/transaction/<int:acquirer_id>
    # Overwrite the Json controller for the pay now button
    @http.route()
    def payment_transaction(self, acquirer_id):
        tx = self.payment_transaction_logic(acquirer_id)
        return tx

    # Checkout Page
    @http.route()
    def checkout(self, one_page_checkout=False, **post):
        cr, uid, context = request.cr, request.uid, request.context

        # Render the Checkout Page
        checkout_page = super(website_sale_donate, self).checkout(**post)

        if post and post.get('acquirer'):
            checkout_page.qcontext.update({'acquirer_id': post.get('acquirer')})

        # If One-Page-Checkout is enabled and checkout_page is not just a redirection or if one_page_checkout in post
        if (request.website['one_page_checkout'] or one_page_checkout) and hasattr(checkout_page, 'qcontext'):

            # Make sure one one_page_checkout is true and in the qcontext
            checkout_page.qcontext['one_page_checkout'] = True

            # Checkout-Page was already called and now submits it's form data
            if post:

                # STEP 1: Update Delivery Method through payment controller
                carrier_id = post.get('delivery_type')
                if carrier_id:
                    post['carrier_id'] = int(carrier_id)
                    self.payment(**post)
                    # HINT: carrier_id must be removed or payment will always return a redirection to /shop/payment
                    post.pop('carrier_id')

                # STEP 2: confirm_order
                # confirm_order validates the form-data and creates or updates partner and sales-order
                confirm_order = self.confirm_order(**post)
                # HINT: opc_payment will also validate if the acquirer is correct for the payment interval of the so
                payment_page = self.opc_payment(**post)
                # Process the checkout controller again to include possible changes made by confirm_order
                checkout_page = super(website_sale_donate, self).checkout(**post)
                checkout_page.qcontext['one_page_checkout'] = True
                # Add a additional warnings list to the qcontext for the payment_transaction controller
                checkout_page.qcontext['opc_warnings'] = list()
                checkout_page.qcontext.update(confirm_order.qcontext)
                checkout_page.qcontext.update(payment_page.qcontext)
                # On errors return the checkout_page
                if checkout_page.qcontext.get('error') \
                        or confirm_order.location != '/shop/payment' \
                        or payment_page.qcontext.get('errors'):
                    _logger.warning(_('Errors in checkout fields or from confirm_order or payment controller found!'))
                    return checkout_page
                # STEP 2: END (SUCCESSFUL)

                # STEP 3: payment_transaction
                # Create or update the Payment-Transaction and update the Sales Order
                # HINT: Normally done by a json request before the pay-now form get's auto submitted by Java Script
                if not post.get('acquirer'):
                    _logger.error(_('No Acquirer (Payment Method) selected!'))
                    # TODO: Check what happens if a 'wrong' acquirer was set at a product_page with ppt_opc
                    checkout_page.qcontext['opc_warnings'].append(_('Please select a payment method.'))
                    return checkout_page

                # HINT: SEEMS THAT THE JSON REQUEST KILLS THE SESSION AND THEREFORE THE SALES ORDER
                #       Because of this and to integrate website_sale_payment_fix the logic was added in a new mehtod
                acquirer_id = int(post.get('acquirer'))
                request.session['acquirer_id'] = acquirer_id
                checkout_page.qcontext.update({'acquirer_id': request.session.get('acquirer_id')})

                self.payment_transaction_logic(acquirer_id, checkout_page=checkout_page)
                # If any errors are found return the checkout_page
                if checkout_page.qcontext.get('opc_warnings'):
                    return checkout_page
                # STEP 3: END (SUCCESSFUL)

                # STEP 4: set sales order to "send" and redirect to the payment provider
                # Open the payment provider page OR directly validate the sales order if amount.total is 0
                # Return the checkout page and auto submit the correct Pay-Now_Button_Form by java script
                # TODO: if amount.total == 0 Directly set sales order to done and redirect to /shop/payment/validate
                # TODO: Also check this behaviour if not One-Page-Checkout !!!
                for acquirer in payment_page.qcontext['acquirers']:
                    if int(acquirer.id) == int(post.get('acquirer')):
                        checkout_page.qcontext['acquirer_auto_submit'] = acquirer
                return checkout_page

            # Checkout-Page is called for the first time (with no post data)
            else:
                payment_page = self.opc_payment()
                checkout_page.qcontext.update(payment_page.qcontext)
                return checkout_page

        return checkout_page

    # One-Page-Checkout: Payment Page Redirection
    # HINT: Shopping Cart Redirection is done above around line 92
    @http.route()
    def payment(self, **post):

        # For one page checkout redirect to checkout page
        if request.website['one_page_checkout']:
            return request.redirect("/shop/checkout")

        # Call super().payment and render correct payment provider buttons
        return self.opc_payment(**post)

    # Alternative confirmation page for Dadi Payment-Providers (Acquirers ogonedadi and frst for now)
    # HINT this rout is called by the payment_provider routes e.g.: ogonedadi_form_feedback or frst_form_feedback
    @http.route(['/shop/confirmation_static'], type='http', auth="public", website=True)
    def payment_confirmation_static(self, order_id=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        try:
            order_id = int(order_id)
            order = request.registry['sale.order'].browse(cr, SUPERUSER_ID, order_id, context=context)[0]
            if order and order.name and order.payment_tx_id:
                return request.website.render("website_sale_donate.confirmation_static", {'order': order})
            else:
                raise
        except:
            return request.website.render("website_sale_donate.confirmation_static", {'order': None})

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
                    'fore_name_web': order.partner_id.fore_name_web,
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
                    'fore_name_web': order.partner_invoice_id.fore_name_web,
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
                    'fore_name_web': order.partner_shipping_id.fore_name_web,
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
