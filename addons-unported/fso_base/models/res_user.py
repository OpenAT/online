# -*- coding: utf-'8' "-*-"
from openerp import models, fields


# Additional fields for Fundraising Studio
class ResUsers(models.Model):
    _inherit = 'res.users'

    active_directory_name = fields.Char(string="Active Directory Name", readonly=True,
                                        help="Fundraising Studio Active Directory Name")
