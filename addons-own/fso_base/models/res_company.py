# -*- coding: utf-8 -*-
from openerp import models, fields


class CompanyInstanceSettings(models.Model):
    _inherit = 'res.company'

    instance_base_port = fields.Char(string='Instance Base Port', size=5)
    instance_id = fields.Char(string='Instance ID (e.g.: dadi)', size=5)

