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
from datetime import timedelta
from openerp import api, models, fields
from openerp.exceptions import ValidationError


class ResPartnerFSToken(models.Model):
    _name = 'res.partner.fstoken'

    name = fields.Char(string='FS Partner Token', required=True,
                       index=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner',
                                 required=True, ondelete='cascade',
                                 index=True)
    expiration_date = fields.Date(string="Expiration Date", required=True,
                                  default=fields.datetime.now() + timedelta(days=14),
                                  index=True)
    fs_origin = fields.Char(string="FS Origin", help="The Fundraising Studio activity ID")
    max_checks = fields.Integer(string="Max checks", default=1,
                                help="Maximum number of checks. If this is higher than number_of_checks the token is"
                                     "counted as expired!")

    # Usage statistics from the fs_ptkone usage log
    log_ids = fields.One2many(comodel_name='res.partner.fstoken.log', inverse_name='fs_ptoken_id')
    last_datetime_of_use = fields.Datetime(string="Last Date and Time of Use",
                                           compute="_compute_usage_statistic")
    first_datetime_of_use = fields.Datetime(string="First Date and Time of Use",
                                            compute="_compute_usage_statistic")
    number_of_checks = fields.Integer(string="Number of checks",
                                      compute="_compute_usage_statistic")

    # Two factor authentication
    # TODO: tfa_type: "enter_string" > Create web form to enter the tfa string and update fstoken_check()
    tfa_type = fields.Selection(selection=[('approved_partner_email', 'Approved Partner E-Mail'),
                                           ('enter_string', 'Enter String')],
                                string="Two Factor Authentication Type")
    tfa_string = fields.Char(string="Two Factor Authentication String",
                             help='If "tfa_type" is "approved_partner_email" the "tfa_string" must contain '
                                  'the main e-mail of the partner at the time the res.partner.fstoken record '
                                  'is created!')
    # Information for the webpage with the online-form where the user could enter the 'tfa_string'
    # EXAMPLE: tfa_type = 'enter_string',
    #          tfa_string = '5693', tfa_label = 'Please enter the last four digits of you bank account', tfa_help = ''
    tfa_label = fields.Char(string="Two Factor Authentication Label",
                                   help='The Label of the Input field')
    tfa_help = fields.Html(string='Two Factor Authentication Help',
                           help="Additional help text or information for the two factor authentication")

    # https://www.odoo.com/documentation/8.0/howtos/backend.html
    @api.constrains('name')
    def _check_fstoken_format(self):
        for record in self:
            if len(record.name) < 9:
                raise ValidationError("FS Partner Token is too short (9 char min): %s" % record.name)
            if not record.name.isalnum():
                raise ValidationError("FS Partner Token must be alphanumeric: %s" % record.name)

    @api.constrains('tfa_type', 'tfa_string')
    def _check_fstoken_tfa(self):
        for record in self:
            if record.tfa_type or record.tfa_string:
                if not record.tfa_type:
                    raise ValidationError("Two Factor Authentication 'tfa_string' is set but 'tfa_type' is missing!")
                if not record.tfa_string:
                    raise ValidationError("Two Factor Authentication 'tfa_type' is set but 'tfa_string' is missing!")

    @api.multi
    def _compute_usage_statistic(self):
        for token in self:
            token.number_of_checks = len(token.log_ids) or 0

            sorted_logs = token.log_ids.sorted()
            token.last_datetime_of_use = sorted_logs[0].log_date if sorted_logs else False
            token.first_datetime_of_use = sorted_logs[-1].log_date if sorted_logs else False

    # https://www.postgresql.org/docs/9.3/static/ddl-constraints.html
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', "FS Tokens must be unique!"),
    ]
