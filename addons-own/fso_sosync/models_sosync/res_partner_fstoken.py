# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerFSToken(models.Model):
    _name = "res.partner.fstoken"
    _inherit = ["res.partner.fstoken", "base.sosync"]

    name = fields.Char(sosync="True")
    expiration_date = fields.Date(sosync="True")
    fs_origin = fields.Char(sosync="True")

    last_datetime_of_use = fields.Datetime(sosync="fson-to-frst")
    first_datetime_of_use = fields.Datetime(sosync="fson-to-frst")
    number_of_checks = fields.Integer(sosync="fson-to-frst")
