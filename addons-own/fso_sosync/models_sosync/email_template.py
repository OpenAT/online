# -*- coding: utf-'8' "-*-"
from openerp import models, fields, api


class EmailTemplateSosync(models.Model):
    _name = "email.template"
    _inherit = ["email.template", "base.sosync"]

    # Set a VERY high sync job priority for async sync job submission by addon 'fso_sosync_async'
    # or at least to be in the first jobs for regular cron bulk submission if the addon is not installed
    _sync_job_priority = 1000000

    # Standard fields
    name = fields.Char(sosync="True")  # Name
    subject = fields.Char(sosync="True")  # EmailBetreff
    email_from = fields.Char(sosync="True")  # EmailVon
    reply_to = fields.Char(sosync="True")  # EmailAntwortAn

    fso_template_view_id = fields.Many2one(sosync="fson-only")   # Not Synced! by useful for syncjob creation
    body_html = fields.Html(sosync="fson-only")                  # Not synced! but useful for syncjob creation

    fso_email_html_parsed = fields.Text(sosync="fson-to-frst")      # e-mail body html to be used by multimailer

