# -*- coding: utf-8 -*-

from openerp import api, fields, models


class ResPartnerTwitch(models.Model):
    _inherit = 'res.partner'

    twitch_username = fields.Char(string='Twitch User Name')
