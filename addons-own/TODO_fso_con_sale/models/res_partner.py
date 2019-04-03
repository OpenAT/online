# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerAltruja(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    altruja_ids = fields.One2many(comodel_name="altruja", inverse_name="partner_id")
