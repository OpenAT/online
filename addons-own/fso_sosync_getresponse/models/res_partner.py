# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerGetResponseSosync(models.Model):
    _inherit = "res.partner"

    getresponse_tag_ids = fields.Many2many(sosync="True")
