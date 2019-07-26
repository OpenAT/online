# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class EmailTemplateFsoForms(models.Model):
    _name = "email.template"
    _inherit = "email.template"

    confirmation_email_template_fso_forms = fields.One2many(comodel_name="fson.form",
                                                            inverse_name="confirmation_email_template",
                                                            readonly=True, index=True)

    information_email_template_fso_forms = fields.One2many(comodel_name="fson.form",
                                                           inverse_name="information_email_template",
                                                           readonly=True, index=True)