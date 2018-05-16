# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class EmailTemplateSosync(models.Model):
    _name = "email.template"
    _inherit = ["email.template", "base.sosync"]

    # Standard fields
    name = fields.Char(sosync="True")  # Name
    subject = fields.Char(sosync="True")  # EmailBetreff
    email_from = fields.Char(sosync="True")  # EmailVon
    reply_to = fields.Char(sosync="True")  # EmailAntwortAn
    fso_template_view_id = fields.Many2one(sosync=True)
    body_html = fields.Html(sosync="True")
    fso_email_html_parsed = fields.Text(sosync="True")  # EmailHTML
