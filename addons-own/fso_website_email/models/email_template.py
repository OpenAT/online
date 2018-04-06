# -*- coding: utf-8 -*-

from openerp import models, fields


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    theme_head = fields.Text(string="<head> content")
    theme_body_attributes = fields.Char(string="<body> Attributes")
