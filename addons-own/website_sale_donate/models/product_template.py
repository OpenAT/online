# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields
from openerp.tools.translate import _

__author__ = 'Michael Karrer'


# Product Template
# ATTENTION: There are unported parts for product.template in website_sale_donate.py !
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    _step_config_fields = ['hide_cart_indicator', 'cart_indicator_name',
                           'hide_product_indicator', 'product_indicator_name',
                           'hide_checkout_indicator', 'checkout_indicator_name',
                           'hide_payment_indicator', 'payment_indicator_name',
                           'hide_confirmation_indicator', 'confirmation_indicator_name']

    website_published_start = fields.Datetime('Website Published Start')
    website_published_end = fields.Datetime('Website Published End')
    website_visible = fields.Boolean('Visible in Website (computed)', readonly=True,
                                     compute="compute_website_visible", store=True)

    # Shop Step/Page Indicator Setup
    step_indicator_setup = fields.Boolean(string="Individual Step-Indicator Setup")

    step_indicator_ul_class = fields.Char(string="Step-Indicator <ul> classes")

    hide_cart_indicator = fields.Boolean(string='Hide Cart Indicator')
    cart_indicator_name = fields.Char(string='Cart Indicator Name', translate=True, default=_('Donation Cart'))

    hide_product_indicator = fields.Boolean(string='Hide Product Indicator')
    product_indicator_name = fields.Char(string='Product Indicator Name', translate=True, default=_('1. Donation Page'))

    hide_checkout_indicator = fields.Boolean(string='Hide Checkout Indicator')
    checkout_indicator_name = fields.Char(string='Checkout Indicator Name', translate=True, default=_('2. Checkout'))

    hide_payment_indicator = fields.Boolean(string='Hide Payment Indicator')
    payment_indicator_name = fields.Char(string='Payment Indicator Name', translate=True, default=_('3. Payment'))

    hide_confirmation_indicator = fields.Boolean(string='Hide Confirmation Indicator')
    confirmation_indicator_name = fields.Char(string='Confirmation Indicator Name', translate=True, default=_('4. Confirmation'))

    # Custom Checkout Fields by product
    checkout_form_id = fields.Many2one(string="Checkout Fields Form", comodel_name='fson.form',
                                       domain="[('product_template_ids', '!=', False)]",
                                       help="Set custom checkout fields for this product")

    # Custom Checkout Giftee Fields by product
    giftee_form_id = fields.Many2one(string="Giftee Fields Form", comodel_name='fson.form',
                                     domain="[('ptemplate_giftee_ids', '!=', False)]",
                                     help="Set custom giftee fields for this product")

    giftee_email_template = fields.Many2one(string="Giftee Info E-Mail",
                                            comodel_name='email.template',
                                            inverse_name="giftee_product_template_ids",
                                            copy=True)

    giftee_checkbox_text = fields.Char(string="Giftee-Checkbox Text", translate=True)

    # Custom donation input template (arbitrary price and donation buttons in checkout box)
    # HINT: dit stands for donation input template
    donation_input_template = fields.Selection(string="Donation Input Template",
                                               selection=[('website_sale_donate.dit_advanced', 'Advanced'),
                                                          ])

    auto_recompute_price_donate = fields.Boolean(string="Auto recompute Price Donate",
                                                 help="Recompute price-donate value on payment interval change")

    # Custom page themes
    # ATTENTION: The name of the theme will be added to the <body> tag if you are on the product page
    #            or a product is in the sale order (check templates.xml)
    #            Use this extra hook for custom css styles! for product page and checkout step pages!
    #            Only products with the same themes can be in the shopping cart - if a product with a different
    #            theme is added it will automatically remove non matching products from the cart!
    #            Todo: We may keep products with different themes in the cart in the future but use the latest theme
    website_theme = fields.Selection(string='Custom CSS Theme',
                                     selection=[('', 'No Custom Theme')],
                                     help="Adds a custom attribute to the <body> tag to be used in CSS selectors!")

    # Clear all other products from the shopping cart (sale order) when this product is added
    clear_cart = fields.Boolean(string="Clear Shopping Cart",
                                help="Clear all other products from the shopping cart (sale order) when this "
                                     "product is added")

    # Thank you page per product
    redirect_url_after_form_feedback = fields.Char(string='Redirect URL after PP Form-Feedback',
                                                   help='Redirect to this URL after processing the Answer of the '
                                                        'Payment Provider instead of /shop/confirmation_static. '
                                                        '(This is the thank you page after a successful '
                                                        'donation/purchase)',
                                                   translate=True)

    @api.constrains('website_theme', 'public_categ_ids')
    def contraint_website_theme(self):
        for r in self:
            if r.website_theme and r.public_categ_ids:
                raise AssertionError(_("You can not add a product with a custom css theme to a shop category!"))

    @api.depends('active', 'website_published', 'website_published_start', 'website_published_end')
    def compute_website_visible(self):
        for pt in self:
            now = fields.Datetime.now()
            if pt.active and pt.website_published and (
                        (not pt.website_published_start or pt.website_published_start <= now)
                    and (not pt.website_published_end or pt.website_published_end > now)):
                pt.website_visible = True
            else:
                pt.website_visible = False

    @api.onchange('fs_product_type')
    def _onchange_set_fs_workflow_by_fs_product_type(self):
        if self.fs_product_type in ['donation', 'godparenthood', 'sponsorship', 'membership']:
            self.fs_workflow = 'donation'
        else:
            self.fs_workflow = 'product'

    # CRUD and COPY
    # -------------
    @api.multi
    def write(self, vals):
        if vals and 'fs_product_type' in vals and not 'fs_workflow' in vals:
            if vals.get('fs_product_type') in ['donation', 'godparenthood', 'sponsorship', 'membership']:
                vals['fs_workflow'] = 'donation'
            else:
                vals['fs_workflow'] = 'product'
        return super(ProductTemplate, self).write(vals)

    @api.multi
    def copy(self, default=None):
        default = default if default else {}

        # TODO: Create copy of the donation buttons
        # TODO: Create cops of the payment methods
        # TODO: Create copy of the payment intervals

        return super(ProductTemplate, self).copy(default=default)


    # Custom Checkout Fields Form Button Action
    # -----------------------------------------
    # TODO: Add frontend validations
    @api.multi
    def create_checkout_fields_form(self):
        for r in self:
            if not r.checkout_form_id:
                # Create the fso form
                res_partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')])

                form_vals = {'name': _('Checkout fields form for product %s (id %s)') % (r.name, r.id),
                             'model_id': res_partner_model.id,
                             'submit_button_text': _('Continue'),
                             'clear_session_data_after_submit': True,
                             'edit_existing_record_if_logged_in': False,
                             'email_only': False,
                             'thank_you_page_edit_data_button': False,
                             #'thank_you_page_edit_redirect': '/fso/subscription/%s' % r.id,
                             #'submission_url': '/fso/subscription/%s' % r.id
                             }

                form = self.env['fson.form'].create(form_vals)

                # Create the fso form fields
                f_fields = {'firstname': {'sequence': 10,
                                          'show': True,
                                          'label': _('Firstname'),
                                          'mandatory': False,
                                          'css_classes': 'col-sm-6 col-md-6 col-lg-6',
                                          'clearfix': False},
                            'lastname': {'sequence': 20,
                                         'show': True,
                                         'label': _('Lastname'),
                                         'mandatory': True,
                                         'css_classes': 'col-sm-6 col-md-6 col-lg-6',
                                         'clearfix': True},
                            'email': {'sequence': 30,
                                      'label': _('E-Mail'),
                                      'show': True,
                                      'mandatory': True,
                                      'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                      'clearfix': True},
                            'birthdate_web': {'sequence': 40,
                                              'label': _('Birthdate'),
                                              'show': True,
                                              'mandatory': False,
                                              'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                              'clearfix': True,
                                              'information': """ Um ihre Spenden von der Steuer absetzten zu können 
                                                                 ist die Angabe ihres Geburtsdatums erforderlich. """},
                            'country_id': {'sequence': 50,
                                           'label': _('Country'),
                                           'show': True,
                                           'mandatory': True,
                                           'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                           'clearfix': True},
                            'donation_deduction_optout_web': {'sequence': 60,
                                                              'label': _('Meine Spenden nicht absetzen'),
                                                              'show': True,
                                                              'mandatory': False,
                                                              'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                                              'clearfix': True,
                                                              'information': """ Bitte anhaken wenn Sie nicht möchten 
                                                                                 das Ihre Spenden automatisch abgesetzt 
                                                                                 werden. """},
                            }
                fields_obj = self.env['ir.model.fields']
                form_field_obj = self.env['fson.form_field']
                for f, vals in f_fields.iteritems():
                    vals['form_id'] = form.id
                    vals['field_id'] = fields_obj.search([('model_id', '=', res_partner_model.id),
                                                          ('name', '=', f)]).id
                    form_field_obj.create(vals)

                # Add this form to the product template
                r.write({'checkout_form_id': form.id})


    @api.multi
    def create_giftee_fields_form(self):
        for r in self:
            if not r.giftee_form_id:
                # Create the fso form
                res_partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')])

                form_vals = {'name': _('Giftee fields form for product %s (id %s)') % (r.name, r.id),
                             'model_id': res_partner_model.id,
                             'submit_button_text': _('Continue'),
                             'clear_session_data_after_submit': True,
                             'edit_existing_record_if_logged_in': False,
                             'email_only': False,
                             'thank_you_page_edit_data_button': False,
                             #'thank_you_page_edit_redirect': '/fso/subscription/%s' % r.id,
                             #'submission_url': '/fso/subscription/%s' % r.id
                             }

                form = self.env['fson.form'].create(form_vals)

                # Create the fso form fields
                f_fields = {'firstname': {'sequence': 10,
                                          'show': True,
                                          'label': _('Firstname'),
                                          'mandatory': False,
                                          'css_classes': 'col-sm-6 col-md-6 col-lg-6',
                                          'clearfix': False},
                            'lastname': {'sequence': 20,
                                         'show': True,
                                         'label': _('Lastname'),
                                         'mandatory': True,
                                         'css_classes': 'col-sm-6 col-md-6 col-lg-6',
                                         'clearfix': True},
                            'email': {'sequence': 30,
                                      'label': _('E-Mail'),
                                      'show': True,
                                      'mandatory': True,
                                      'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                      'clearfix': True},
                            'birthdate_web': {'sequence': 40,
                                              'label': _('Birthdate'),
                                              'show': True,
                                              'mandatory': False,
                                              'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                              'clearfix': True,
                                              'information': """ Um ihre Spenden von der Steuer absetzten zu können 
                                                                 ist die Angabe ihres Geburtsdatums erforderlich. """},
                            'country_id': {'sequence': 50,
                                           'label': _('Country'),
                                           'show': True,
                                           'mandatory': True,
                                           'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                           'clearfix': True},
                            }
                fields_obj = self.env['ir.model.fields']
                form_field_obj = self.env['fson.form_field']
                for f, vals in f_fields.iteritems():
                    vals['form_id'] = form.id
                    vals['field_id'] = fields_obj.search([('model_id', '=', res_partner_model.id),
                                                          ('name', '=', f)]).id
                    form_field_obj.create(vals)

                # Add this form to the product template
                r.write({'giftee_form_id': form.id})
