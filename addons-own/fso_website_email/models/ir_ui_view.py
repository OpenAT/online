# -*- coding: utf-8 -*-

from openerp import models, fields


class ViewEmailTemplate(models.Model):
    _inherit = 'ir.ui.view'

    fso_email_template = fields.Boolean(string='FSON E-Mail Template',
                                        help="Mark this view as a theme for a FS-Online e-mail template")
    fso_email_template_ids = fields.One2many(string='Used in E-Mail Templates',
                                             comodel_name="email.template", inverse_name="fso_template_view_id",)
