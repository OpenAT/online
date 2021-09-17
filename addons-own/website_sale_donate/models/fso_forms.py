# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _inherit = "fson.form"

    type = fields.Selection(selection_add=[('checkout', 'Shop Checkout Fields'),
                                           ('giftee', 'Shop Giftee Fields')])

    product_template_ids = fields.One2many(comodel_name="product.template",
                                           inverse_name="checkout_form_id",
                                           string="Checkout Fields for Product",
                                           help="Configure custom checkout fields for a product in the webshop")

    ptemplate_giftee_ids = fields.One2many(comodel_name="product.template",
                                           inverse_name="giftee_form_id",
                                           string="Giftee Fields for Product",
                                           help="Configure custom giftee fields for a product in the webshop")

    @api.constrains('product_template_ids', 'field_ids')
    def constrain_product_template_ids(self):
        for r in self:

            # Add additional checks for products that are linked to fso_subscriptions (product.template)
            if r.product_template_ids:
                assert r.type == 'checkout', "Form type must be 'Checkout Fields' if linked to product_template_ids!"

                assert not r.ptemplate_giftee_ids, "Form already in use as giftee fields by other product(s)!"

                # Check the form model
                if r.model_id.model != 'res.partner':
                    raise ValidationError("Form model must be 'res.partner' if linked to a "
                                          "product for custom checkout fields!")

                # TODO: Check if all mandatory checkout fields of website_sale_donate are included in the form!

    @api.constrains('ptemplate_giftee_ids', 'field_ids')
    def constrain_ptemplate_giftee_ids(self):
        for r in self:

            # Add additional checks for products that are linked to fso_subscriptions (product.template)
            if r.ptemplate_giftee_ids:
                assert r.type == 'giftee', "Form type must be 'Giftee Fields' if linked to ptemplate_giftee_ids!"

                assert not r.product_template_ids, "Form already in use for custom checkout fields by other product(s)"

                # Check the form model
                if r.model_id.model != 'res.partner':
                    raise ValidationError("Form model must be 'res.partner' if linked to a "
                                          "product for custom giftee fields!")

    @api.constrains('type', 'ptemplate_giftee_ids', 'product_template_ids')
    def constrain_type(self):

        # TODO: Check if all mandatory giftee fields for a res.partner are included and enabled in the form instead of
        #       just name and country!
        def check_mandatory_shop_fields(form):
            field_names = r.mapped('field_ids.name')
            assert 'country_id' in field_names, (
                "country_id field must exists in the %s form fields" % form.type)

            assert 'firstname' in field_names or 'lastname' in field_names, (
                "'firstname' or 'lastname' field must exist in the %s form fields" % form.type)

        for r in self:
            if r.type == 'giftee' and r.ptemplate_giftee_ids:
                check_mandatory_shop_fields(form=r)
            if r.type == 'checkout' and r.product_template_ids:
                check_mandatory_shop_fields(form=r)

    @api.model
    def compute_type_if_not_set(self):
        # Overwrite from fso_forms to respect the other types too
        checkout_missing = self.search(['|', ('type', '=', ''), ('type', '=', False), ('product_template_ids', '!=', False)])
        logger.info("Found %s forms where type 'checkout' is missing" % len(checkout_missing))
        checkout_missing.write({'type': 'checkout'})

        giftee_missing = self.search(['|', ('type', '=', ''), ('type', '=', False), ('ptemplate_giftee_ids', '!=', False)])
        logger.info("Found %s forms where type 'giftee' is missing" % len(giftee_missing))
        giftee_missing.write({'type': 'giftee'})

        type_missing = self.search(['|', ('type', '=', ''), ('type', '=', False),
                                    ('product_template_ids', '=', False),
                                    ('ptemplate_giftee_ids', '=', False)])
        logger.info("Found %s forms where type 'standard' is missing" % len(type_missing))
        type_missing.write({'type': 'standard'})
