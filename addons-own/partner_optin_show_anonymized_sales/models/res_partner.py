# -*- coding: utf-8 -*-

from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    optin_show_anoym_sales = fields.Boolean(string='Show Anonymized Sales Opt-In',
                                            help="Agreement of the partner to display sales in anonymized forms e.g. "
                                                 "in streams, on social media or on last-donation widgets")
