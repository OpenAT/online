# -*- coding: utf-8 -*-

from openerp import models, fields


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    fso_email_template = fields.Boolean(string='FSON Template')
    fso_template_view_id = fields.Many2one(string='Based on',
                                           comodel_name="ir.ui.view", inverse_name="fso_email_template_ids",
                                           domain="[('fso_email_template','=',True)]")

    theme_head = fields.Text(string="<head> content")

    # TODO: Computed field with final html: fso_email_html
