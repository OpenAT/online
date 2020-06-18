# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResGroupsSosync(models.Model):
    _name = "res.groups"
    _inherit = ["res.groups", "base.sosync"]

    # This model is read-only in FRST

    # Access Group Name
    name = fields.Char(sosync="fson-to-frst")

    # Computed full name field
    full_name = fields.Char(sosync="fson-to-frst")

    # Users
    users = fields.Many2many(sosync="fson-to-frst")
