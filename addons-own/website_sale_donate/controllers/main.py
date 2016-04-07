# -*- coding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from lxml import etree
import copy
import requests

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
        request.session['last_shop_page'] = request.httprequest.base_url + '?' + request.httprequest.query_string
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

        # this will basically pre-render the product page and store it in productpage
        productpage = super(website_sale_donate, self).product(product, category, search, **kwargs)

        # Product Qweb Template based on the product_page_template field
        # HINT: qcontext holds the initial values the qweb template was called with
        # HINT: The first attribute of website.render is the template ID
        if product.product_page_template:
            productpage = request.website.render(product.product_page_template, productpage.qcontext)

        # Add Warnings (e.g. by cart_update)
        productpage.qcontext['warnings'] = kwargs.get('warnings')
        kwargs['warnings'] = None

        # Set a default payment_interval_id: will be rendered as checked in the product page
        if product.payment_interval_ids:
            productpage.qcontext['payment_interval_id'] = product.payment_interval_ids[0].id

        # Get values from sales order line
        sale_order_id = request.session.sale_order_id
        if sale_order_id:
            # Search for a sales order line for the current product in the sales order of the current session
            sol_obj = request.registry['sale.order.line']
            # Get sale order line id if product or variant of product is in active sale order
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

        if request.website['one_page_checkout']:
            return request.redirect("/shop/checkout")

        return cartpage

    # SIMPLE CHECKOUT:
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
    @http.route(['/shop/cart/update'])
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        cr, uid, context = request.cr, request.uid, request.context

        product = request.registry['product.product'].browse(cr, SUPERUSER_ID, int(product_id), context=context)

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
            return request.redirect('/shop/product/%s?&warnings=%s' % (product.product_tmpl_id.id, warnings))

        # Check Payment Interval
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
        if request.session.get('last_page') and request.website['add_to_cart_stay_on_page']:
            return request.redirect(request.session['last_page'])

        # Redirect to the shopping cart
        return request.redirect("/shop/cart")

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
        print "mandatory_bill %s" % mandatory_bill
        return mandatory_bill

    def _get_optional_billing_fields(self):
        billing_fields = request.env['website.checkout_billing_fields']
        billing_fields = billing_fields.search([])
        optional_bill = []
        for field in billing_fields:
            if not field.mandatory:
                optional_bill.append(field.res_partner_field_id.name)
        print "optional_bill %s" % optional_bill
        return optional_bill

    def _get_mandatory_shipping_fields(self):
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([])
        mandatory_ship = []
        for field in shipping_fields:
            if field.mandatory:
                mandatory_ship.append(field.res_partner_field_id.name)
        print "mandatory_ship %s" % mandatory_ship
        return mandatory_ship

    def _get_optional_shipping_fields(self):
        shipping_fields = request.env['website.checkout_shipping_fields']
        shipping_fields = shipping_fields.search([])
        optional_ship = []
        for field in shipping_fields:
            if not field.mandatory:
                optional_ship.append(field.res_partner_field_id.name)
        print "optional_ship %s" % optional_ship
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
            return payment_page

        # Set the current acquirer to be correctly pre selected on subsequent renders of the checkout page
        if post.get('acquirer'):
            payment_qcontext['acquirer_id'] = post.get('acquirer')
            # TODO: If an acquirer and post data is already present we could do form data validation
            # TODO: Should add a new mehtod to payment providers: something like _[paymentmethod]_pre_send_form_validate()
            # TODO: If errors are found we could add them to the errors dict

        # Check for errors in qcontext
        # HINT: If errors are present Pay-Now button forms will NOT! be rendered by payment controller
        if payment_qcontext.get('errors'):
            return payment_page

        # Create alternative Pay-Now buttons (button_opc)
        # Remove the form and submit button, uniquely prefix the acquirer input fields and set data from post
        for acquirer in payment_qcontext['acquirers']:

            # Convert the Pay-Now button forms into input fields without surrounding form tag
            # to insert them into the regular checkout form
            # http://lxml.de/lxmlhtml.html
            # http://lxml.de/tutorial.html
            button = etree.fromstring(acquirer.button)
            assert button.tag == 'form', "ERROR: One Page Checkout: Payment Button has not <form> as root tag!"

            # Process input tags of original button to include post values
            for form_input in button.iter("input"):
                if form_input.get('name'):
                    prefixed_input_name = "aq" + str(acquirer.id) + '_' + str(form_input.get('name'))
                    # Set values from post data if empty in template (e.g.: FRST IBAN and BIC)
                    if not form_input.get('value') and prefixed_input_name in post:
                        form_input.set('value', post.get(prefixed_input_name))

            # Update the original acquirer.button
            acquirer.button = etree.tostring(button, encoding='UTF-8', pretty_print=True)

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

        return payment_page

    # Checkout Page
    @http.route()
    def checkout(self, **post):

        # Store or get Acquirer in/from Session (Payment-Method)
        # if post.get('acquirer'):
        #     request.session['last_acquirer_id'] = post.get('acquirer')
        # elif request.session['last_acquirer_id']:
        #     post['acquirer'] = request.session['last_acquirer_id']

        # Render the Checkout Page
        checkout_page = super(website_sale_donate, self).checkout(**post)

        # If One-Page-Checkout is enabled and checkout_page is not just a redirection
        if request.website['one_page_checkout'] and hasattr(checkout_page, 'qcontext'):

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
                # Validate the checkout page form data and create or update partner and sales order
                confirm_order = self.confirm_order(**post)
                # Check for errors
                if confirm_order.qcontext:
                    if confirm_order.qcontext.get('error'):
                        # Extend qcontext with acquirer data (populated with data from post)
                        payment_page = self.opc_payment(**post)
                        if payment_page.qcontext:
                            # Add the qcontext of the payment page to the checkout page
                            confirm_order.qcontext.update(payment_page.qcontext)
                            # Render the checkout page to show the errors (errors from payment page would be included)
                            # HINT: confirm_order controller renders the checkout page again on errors
                            # HINT: confirm_order controller will not save or update any shippings on error
                            #       therefore adding field_date to shippings is not needed here
                            return confirm_order
                        # On redirections caused by errors found by the payment controller
                        else:
                            return payment_page
                # Check for a different redirection than '/shop/payment' caused by an error
                if hasattr(confirm_order, 'location'):
                    if confirm_order.location != '/shop/payment':
                        # Return the redirection
                        return confirm_order

                # STEP 3: payment
                # Validate the payment page after sale order and partner got created or updated in STEP 1
                payment_page = self.opc_payment(**post)
                # Check for redirections caused by errors
                if not payment_page.qcontext:
                    return payment_page

                # Process the checkout controller again to include possible changes made in STEP 2
                checkout_page = super(website_sale_donate, self).checkout(**post)

                # ATTENTION: Add the qcontext of the payment page to the checkout page (not needed later on)
                checkout_page.qcontext.update(payment_page.qcontext)

                # Check for errors found by the payment controller
                if payment_page.qcontext.get('errors'):
                    # Render the checkout page to show the errors
                    return checkout_page

                # STEP 4: payment_transaction
                # Create or update the Payment-Transaction and update the Sales Order
                # HINT: Normally done by a json request before the pay-now form get's auto submitted by Java Script
                if not post.get('acquirer'):
                    # HINT: payment qcontext was already added in STEP 2
                    return checkout_page
                # TODO: BUGFixing - Transaction is not updated after first creation ? Force update may be needed
                pay_now = self.payment_transaction(int(post.get('acquirer')))
                # Check for redirection caused by errors
                if not isinstance(pay_now, int):
                    return pay_now

                # STEP 5: Open the payment provider page OR directly validate the sales order if amount.total is 0
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
                if hasattr(payment_page, 'qcontext'):
                    # Add the qcontext of the payment page to the checkout page
                    checkout_page.qcontext.update(payment_page.qcontext)
                    # Render the checkout page
                    return checkout_page
                # On error
                else:
                    # Return the redirection caused by the payment controller
                    return payment_page

        return checkout_page

    # Payment Page
    @http.route()
    def payment(self, **post):
        res = super(website_sale_donate, self).payment(**post)
        if request.website['one_page_checkout']:
            return request.redirect("/shop/checkout")
        return res

    # HINT: Shopping Cart Redirection is done above around line 92
