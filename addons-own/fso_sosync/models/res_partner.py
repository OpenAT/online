# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "base.sosync"]

    name = fields.Char(sosync="True")
    firstname = fields.Char(sosync="True")
    lastname = fields.Char(sosync="True")
