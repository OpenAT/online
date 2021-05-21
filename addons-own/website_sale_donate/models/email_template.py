# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class EmailTemplateWebsiteSaleDonate(models.Model):
    _name = "email.template"
    _inherit = "email.template"

    giftee_product_template_ids = fields.One2many(comodel_name="product.template",
                                                  inverse_name="giftee_email_template",
                                                  readonly=True)
