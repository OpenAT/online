# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _inherit = "fson.form"

    product_template_ids = fields.One2many(comodel_name="product.template",
                                           inverse_name="checkout_form_id",
                                           string="Checkout Fields for Product",
                                           help="Configure custom checkout fields for a product in the webshop")

    @api.constrains('product_template_ids', 'field_ids')
    def contrains_product_template_ids(self):
        for r in self:
            if len(r.product_template_ids) > 1:
                raise ValidationError("You can only link one product to this form")

            # Add additional checks for products that are linked to fso_subscriptions (product.template)
            if len(r.product_template_ids) == 1:

                # Check the form model
                if r.model_id.model != 'res.partner':
                    raise ValidationError("Form model must be 'res.partner' if linked to a "
                                          "product for custom checkout fields!")

                # TODO: Check if all mandatory checkout fields of website_sale_donate are included in the form!

