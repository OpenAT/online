# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerGetResponseSosync(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "base.sosync"]

    getresponse_tag_ids = fields.Many2many(sosync="True")
