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
import datetime
from datetime import timedelta
import time

import openerp
from openerp import api, models, fields
from openerp.exceptions import ValidationError, AccessDenied
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.auth_partner.fstoken_tools import fstoken_check


class res_users(models.Model):
    _inherit = 'res.users'

    # Extend the check_credentials method to work with FS-Tokens also
    # HINT: check openerp/addons/base/res/res_users.py for more info
    def check_credentials(self, cr, uid, password):
        try:
            # Try regular or other auth methods
            return super(res_users, self).check_credentials(cr, uid, password)
        except AccessDenied:
            # Check for a valid FS-Token
            token_record, user_record, errors = fstoken_check(password)
            if errors:
                raise openerp.exceptions.AccessDenied()


class ResPartnerFSToken(models.Model):
    _name = 'res.partner.fstoken'

    name = fields.Char(string='FS Partner Token', required=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner',
                                 required=True, ondelete='cascade')
    expiration_date = fields.Date(string="Expiration Date", required=True,
                                  default=fields.datetime.now() + timedelta(days=14))
    fs_origin = fields.Char(string="FS Origin")
    last_date_of_use = fields.Date(string="DEPRICATED: Last Date of Use", readonly=True)
    last_datetime_of_use = fields.Datetime(string="Last Date and Time of Use", readonly=True)
    first_datetime_of_use = fields.Datetime(string="First Date and Time of Use", readonly=True)
    number_of_checks = fields.Integer(string="Number of checks", default=0, redonly=True)

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

    fstoken_ids = fields.One2many(string='FS Partner Tokens', comodel_name='res.partner.fstoken',
                                  inverse_name='partner_id')

