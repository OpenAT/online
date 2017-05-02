# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'

from openerp import models, fields, api

# Port to odoo v8 api
class Website(models.Model):
    _inherit = 'website'

    # SHOP SETTINGS
    one_page_checkout = fields.Boolean(string='One-Page-Checkout')
    add_to_cart_stay_on_page = fields.Boolean(string='Add to Cart and stay on Page')
    button_login = fields.Char(string='Login Button', translate=True)
    button_logout = fields.Char(string='Logout Button', translate=True)
    button_back_to_page = fields.Char(string='Back to Page Button', translate=True)
    square_image_x = fields.Integer(string='Product SquareImage x-Size in Pixel', default=400)
    square_image_y = fields.Integer(string='Product SquareImage y-Size in Pixel', default=400)

    # SHOP CART
    # Cart Page
    cart_indicator = fields.Char(string='Indicator Cart', translate=True)
    cart_page_header = fields.Char(string='Cart Page Main Header', translate=True)
    button_cart_to_data = fields.Char(string='Cart to Data Button', translate=True)
    cart_page_top = fields.Html(string='Cart Page Top Snippet Dropping Area', translate=True)
    cart_page_bottom = fields.Html(string='Cart Page Bottom Snippet Dropping Area', translate=True)
    # Small Cart
    small_cart_title = fields.Char(string='Small Cart Title', translate=True)

    # SHOP CHECKOUT
    # Checkout Form
    amount_title = fields.Char(string='Amount (Checkoutbox) Form-Title', translate=True)
    checkout_title = fields.Char(string='Your Data Form-Title', translate=True)
    delivery_title = fields.Char(string='Delivery-Option Form-Title', translate=True)
    payment_title = fields.Char(string='Payment-Option Form-Title', translate=True)
    country_default_value = fields.Many2one(comodel_name='res.country', string='Default country for checkout page')
    hide_shipping_address = fields.Boolean(string='Hide Shipping Address')
    hide_delivery_methods = fields.Boolean(string='Hide Delivery Methods')
    checkoutbox_footer = fields.Html(string='Global Footer for the Checkoutbox', translate=True)
    # Checkout Page
    checkout_indicator = fields.Char(string='Indicator Checkout', translate=True)
    checkout_page_header = fields.Char(string='Checkout Page Main Header', translate=True)
    checkout_show_login_button = fields.Boolean(string='Show Login Button on Checkout Page')
    button_data_to_payment = fields.Char(string='Data to Payment Button', translate=True)
    checkout_page_top = fields.Html(string='Checkout Page Top Snippet Dropping Area', translate=True)
    checkout_page_bottom = fields.Html(string='Checkout Page Bottom Snippet Dropping Area', translate=True)

    # SHOP PAYMENT
    # Payment Form
    acquirer_default = fields.Many2one(comodel_name='payment.acquirer', string='Default Payment Method')
    payment_interval_default = fields.Many2one(comodel_name='product.payment_interval',
                                               string='Default Payment Interval')
    payment_interval_as_selection = fields.Boolean(string='Payment Interval as Selection List')
    # Payment Page
    payment_indicator = fields.Char(string='Indicator Payment', translate=True)
    payment_page_header = fields.Char(string='Payment Page Main Header', translate=True)
    payment_page_top = fields.Html(string='Payment Page Top Snippet Dropping Area', translate=True)
    payment_page_bottom = fields.Html(string='Payment Page Bottom Snippet Dropping Area', translate=True)
    # Payment Settings
    redirect_url_after_form_feedback = fields.Char(string='Redirect URL after PP Form-Feedback',
                                                   help='Redirect to this URL after processing the Answer of the '
                                                        'Payment Provider instead of /shop/confirmation_static',
                                                   translate=True)

    # SHOP CONFIRMATION STATIC (DADI PAYMENT PROVIDERS)
    confirmation_indicator = fields.Char(string='Indicator Confirmation', translate=True)
    confirmation_page_header = fields.Char(string='Confirmation Page Main Header', translate=True)
    confirmation_page_top = fields.Html(string='Confirmation Page Top Snippet Dropping Area', translate=True)
    confirmation_page_bottom = fields.Html(string='Confirmation Page Bottom Snippet Dropping Area', translate=True)

    # WEBSITE SETTINGS FORM RELATED MODELS
    @api.model
    def _default_order_email(self):
        return self.env.ref('sale.email_template_edi_sale')

    OrderEmail = fields.Many2one(comodel_name="email.template", string="Sale Order E-Mail Template",
                                 default=_default_order_email, readonly=True)
    OrderEmailPartnerTo = fields.Char(related="OrderEmail.partner_to", readonly=True)
    OrderEmailSubject = fields.Char(related="OrderEmail.subject", readonly=True)
    OrderEmailBody = fields.Html(related="OrderEmail.body_html", readonly=True)

    @api.model
    def _default_status_email(self):
        return self.env.ref('website_sale_donate.email_template_webshop')

    StatusEmail = fields.Many2one(comodel_name="email.template", string="Payment Status E-Mail Template",
                                  default=_default_status_email, readonly=True)
    StatusEmailPartnerTo = fields.Char(related="StatusEmail.partner_to", readonly=True)
    StatusEmailSubject = fields.Char(related="StatusEmail.subject", readonly=True)
    StatusEmailBody = fields.Html(related="StatusEmail.body_html", readonly=True)

    # Computed fields for tree views in website settings form view
    @api.multi
    def _all_payment_acquirers(self):
        payment_acquirers = self.env['payment.acquirer'].search([])
        for rec in self:
            rec.PaymentAcquirers = payment_acquirers

    PaymentAcquirers = fields.Many2many(comodel_name='payment.acquirer',
                                        string="Payment Acquirers",
                                        compute="_all_payment_acquirers", readonly=True)

    @api.multi
    def _all_payment_intervals(self):
        payment_intervals = self.env['product.payment_interval'].search([])
        for rec in self:
            rec.PaymentIntervals = payment_intervals

    PaymentIntervals = fields.Many2many(comodel_name='product.payment_interval',
                                        string="Payment Intervals",
                                        compute="_all_payment_intervals", readonly=True)

    @api.multi
    def _all_checkout_fields(self):
        checkout_fields = self.env['website.checkout_billing_fields'].search([])
        for rec in self:
            rec.CheckoutFields = checkout_fields

    CheckoutFields = fields.Many2many(comodel_name='website.checkout_billing_fields',
                                      string="Checkout Fields",
                                      compute="_all_checkout_fields", readonly=True)

    @api.multi
    def _all_shipping_fields(self):
        shipping_fields = self.env['website.checkout_shipping_fields'].search([])
        for rec in self:
            rec.ShippingFields = shipping_fields

    ShippingFields = fields.Many2many(comodel_name='website.checkout_shipping_fields',
                                      string="Shipping Fields",
                                      compute="_all_shipping_fields", readonly=True)
