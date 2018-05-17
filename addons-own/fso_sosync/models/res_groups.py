# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResGroupsSosync(models.Model):
    _name = "res.groups"
    _inherit = ["res.groups", "base.sosync"]

    # Access Group Name
    name = fields.Char(sosync="True")

    # Computed full name field
    full_name = fields.Char(sosync="True")

    # Users
    users = fields.Many2many(sosync="True")
