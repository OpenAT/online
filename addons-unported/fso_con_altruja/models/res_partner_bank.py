# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerAltruja(models.Model):
    _name = "res.partner.bank"
    _inherit = "res.partner.bank"

    altruja_ids = fields.One2many(comodel_name="altruja", inverse_name="bank_id")
