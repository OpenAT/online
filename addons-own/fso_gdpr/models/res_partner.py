# -*- coding: utf-'8' "-*-"
from openerp import models


# Additional fields for the web checkout
class ResPartnerGDPRBase(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'gdpr.base']
