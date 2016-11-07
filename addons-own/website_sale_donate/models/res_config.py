from openerp.osv import fields, osv


class website_sale_donate_config_settings(osv.osv_memory):
    _inherit = 'website.config.settings'

    _columns = {
        # HINT: in addon website in res_config.py
        # 'website_id': fields.many2one('website', string="website", required=True),
        # defaults={'website_id': lambda self,cr,uid,c: self.pool.get('website').search(cr, uid, [], context=c)[0],}
        #
        # Checkout Pages Headers
        'cart_page_header': fields.related('website_id', 'cart_page_header', type="char",
                                           string='Cart Page Main Header', translate=True),
        'checkout_page_header': fields.related('website_id', 'checkout_page_header', type="char",
                                               string='Checkout Page Main Header', translate=True),
        'payment_page_header': fields.related('website_id', 'payment_page_header', type="char",
                                              string='Payment Page Main Header', translate=True),
        'confirmation_page_header': fields.related('website_id', 'confirmation_page_header', type="char",
                                                   string='Confirmation Page Main Header', translate=True),
        # Checkout Steps Indicator
        'cart_indicator': fields.related('website_id', 'cart_indicator', type="char",
                                           string='Indicator Cart', translate=True),
        'checkout_indicator': fields.related('website_id', 'checkout_indicator', type="char",
                                               string='Indicator Checkout', translate=True),
        'payment_indicator': fields.related('website_id', 'payment_indicator', type="char",
                                              string='Indicator Payment', translate=True),
        'confirmation_indicator': fields.related('website_id', 'confirmation_indicator', type="char",
                                                   string='Indicator Confirmation', translate=True),
        # small-cart-header
        'small_cart_title': fields.related('website_id', 'small_cart_title', type="char",
                                           string='Small Cart Title', translate=True),
        # Section h3's for the custom checkout form
        'amount_title': fields.related('website_id', 'amount_title', type="char",
                                         string='Amount (Checkoutbox) Form-Title', translate=True),
        'checkout_title': fields.related('website_id', 'checkout_title', type="char",
                                         string='Your Data Form-Title', translate=True),
        'delivery_title': fields.related('website_id', 'delivery_title', type="char",
                                         string='Delivery-Option Form-Title', translate=True),
        'payment_title': fields.related('website_id', 'payment_title', type="char",
                                        string='Payment-Option Form-Title', translate=True),
        # Button Text
        'button_login': fields.related('website_id', 'button_login', type="char",
                                         string='Login Button', translate=True),
        'button_logout': fields.related('website_id', 'button_logout', type="char",
                                         string='Logout Button', translate=True),
        'button_back_to_page': fields.related('website_id', 'button_back_to_page', type="char",
                                         string='Back to Page Button', translate=True),
        'button_cart_to_data': fields.related('website_id', 'button_cart_to_data', type="char",
                                        string='Cart to Data Button', translate=True),
        'button_data_to_payment': fields.related('website_id', 'button_data_to_payment', type="char",
                                         string='Data to Payment Button', translate=True),
        # Behaviour
        # Force Default Country  (If GeoIP is NOT working and user did not select any country)
        'country_default_value': fields.related('website_id', 'country_default_value', type="many2one",
                                                relation="res.country", string="Default country for checkout page",
                                                help="Only used if GEO IP is NOT working and no country selected"),
        'acquirer_default': fields.related('website_id', 'acquirer_default', type="many2one",
                                           relation="payment.acquirer", string="Default Payment Method"),
        'payment_interval_default': fields.related('website_id', 'payment_interval_default', type="many2one",
                                           relation="product.payment_interval", string="Default Payment Interval"),
        'payment_interval_as_selection': fields.related('website_id', 'payment_interval_as_selection', type="boolean",
                                                        string='FORCE Payment Interval as Selection List'),
        'add_to_cart_stay_on_page': fields.related('website_id', 'add_to_cart_stay_on_page', type="boolean",
                                                   string='Add to Cart and stay on the Page'),
        'checkout_show_login_button': fields.related('website_id', 'checkout_show_login_button', type="boolean",
                                                     string='Show Login Button on Checkout Page'),
        'one_page_checkout': fields.related('website_id', 'one_page_checkout', type="boolean",
                                            string='One-Page-Checkout'),
        'hide_shipping_address': fields.related('website_id', 'hide_shipping_address', type="boolean",
                                                string='Hide Shipping Address'),
        'hide_delivery_methods': fields.related('website_id', 'hide_delivery_methods', type="boolean",
                                                string='Hide Delivery Methods'),
        'redirect_url_after_form_feedback': fields.related('website_id', 'redirect_url_after_form_feedback',
                                                           type="char",
                                                           string='Redirect URL after PP Form-Feedback',
                                                           help='Redirect to this URL after processing the Answer of '
                                                                'the Payment Provider instead of '
                                                                '/shop/confirmation_static',
                                                           translate=True),
        # Images
        'square_image_x': fields.related('website_id', 'square_image_x', type="integer",
                                         string='Product SquareImage x-Size in Pixel'),
        'square_image_y': fields.related('website_id', 'square_image_y', type="integer",
                                         string='Product SquareImage y-Size in Pixel'),

    }
