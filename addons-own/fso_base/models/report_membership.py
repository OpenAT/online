# -*- coding: utf-'8' "-*-"
from openerp import models, fields


# Additional fields for the web checkout
class ReportMembership(models.Model):
    _inherit = 'report.membership'

    associate_member_id = fields.Many2one(index=True)
