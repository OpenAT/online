# -*- coding: utf-'8' "-*-"
from openerp import models, fields


# Additional fields for Fundraising Studio
class ResUsers(models.Model):
    _inherit = 'res.users'

    active_directory_name = fields.Char(string="Active Directory Name", readonly=True,
                                        help="Fundraising Studio Active Directory Name")

    # This is a "hack" to be able to delete partners that created res.user for website tokens
    # Please check res_partner also to see the unlink() method where a special check for regular users was implemented!
    partner_id = fields.Many2one(ondelete="cascade", index=True)
