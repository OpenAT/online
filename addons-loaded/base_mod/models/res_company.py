# -*- coding: utf-8 -*-
from openerp.osv import osv, fields


class CompanyBasePort(osv.Model):
    _inherit = 'res.company'

    _columns = {
        'instance_base_port': fields.char(string='Instance Base Port', size=5),
    }
