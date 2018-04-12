# -*- coding: utf-8 -*-

from openerp import models, fields


class ViewEmailTemplate(models.Model):
    _inherit = 'ir.ui.view'

    fso_email_template = fields.Boolean(string='FSON E-Mail Template')
    fso_email_template_ids = fields.One2many(string='Used by E-Mails Templates',
                                             comodel_name="email.template", inverse_name="fso_template_view_id",)
