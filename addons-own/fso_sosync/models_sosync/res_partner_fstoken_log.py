# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerFSToken(models.Model):
    _name = "res.partner.fstoken.log"
    _inherit = ["res.partner.fstoken.log", "base.sosync"]

    log_date = fields.Datetime(sosync="fson-to-frst")
    fs_ptoken = fields.Char(sosync="fson-to-frst")
    fs_ptoken_id = fields.Many2one(sosync="fson-to-frst")
    url = fields.Char(sosync="fson-to-frst")
    ip = fields.Char(sosync="fson-to-frst")
    device = fields.Char(sosync="fson-to-frst")
    login = fields.Boolean(sosync="fson-to-frst")
