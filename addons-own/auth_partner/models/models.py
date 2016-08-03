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

from openerp import api, models, fields
from openerp.exceptions import ValidationError
from datetime import timedelta


class ResPartnerFSToken(models.Model):
    _name = 'res.partner.fstoken'

    name = fields.Char(string='FS Partner Token', required=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner',
                                 required=True, ondelete='cascade')
    expiration_date = fields.Date(string="Expiration Date",
                                  default=fields.datetime.now() + timedelta(days=14))
    fs_origin = fields.Char(string="FS Origin")

    # https://www.odoo.com/documentation/8.0/howtos/backend.html
    @api.constrains('name')
    def _check_fstoken_format(self):
        for record in self:
            if len(record.name) < 6:
                raise ValidationError("FS Partner Token is too short (6 char min): %s" % record.name)
            if not record.name.isalnum():
                raise ValidationError("FS Partner Token must be alphanumeric: %s" % record.name)

    # https://www.postgresql.org/docs/9.3/static/ddl-constraints.html
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', "FS Tokens must be unique!"),
    ]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fstoken_ids = fields.One2many(comodel_name='res.partner.fstoken', inverse_name='partner_id')
