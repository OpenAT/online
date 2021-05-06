# -*- coding: utf-8 -*-
##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields


class ResPartnerFSToken(models.Model):
    """ Log of every fs_ptoken usage that lead to a login!
        ATTENTION: Do not log token errors or if already logged in!
    """
    _name = 'res.partner.fstoken.log'
    _rec_name = 'fs_ptoken'
    _order = 'log_date DESC'

    log_date = fields.Datetime(string='Log Date', required=True, index=True)
    fs_ptoken = fields.Char(string='fs_ptoken', required=True, index=True)

    fs_ptoken_id = fields.Many2one(comodel_name='res.partner.fstoken', inverse_name='log_ids', string="Token Record",
                                   ondelete='set null')
    user_id = fields.Many2one(comodel_name='res.users', string='User', ondelete='set null')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', ondelete='set null')

    url = fields.Char(string='URL')
    ip = fields.Char(string='IP')
    device = fields.Char(string='Device')
