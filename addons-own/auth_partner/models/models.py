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
from openerp.exceptions import Warning


class res_users(models.Model):
    _inherit = 'res.users'

    # Extend the check_credentials method to work with FS-Tokens also
    # HINT: check openerp/addons/base/res/res_users.py for more info
    def check_credentials(self, cr, uid, password):
        try:
            # Try regular or other auth methods
            return super(res_users, self).check_credentials(cr, uid, password)
        except AccessDenied:

            # In case there is no request yet (unbound object error catch)
            # https://github.com/OCA/e-commerce/issues/152
            # https://github.com/OCA/e-commerce/pull/190
            if not request:
                #raise openerp.exceptions.AccessDenied()
                raise

            # Check for a valid FS-Token
            token_record, user_record, errors = fstoken_check(password)
            if errors:
                # raise openerp.exceptions.AccessDenied()
                raise


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
    last_date_of_use = fields.Date(string="DEPRICATED: Last Date of Use", readonly=True)
    last_datetime_of_use = fields.Datetime(string="Last Date and Time of Use", readonly=True)
    first_datetime_of_use = fields.Datetime(string="First Date and Time of Use", readonly=True)
    number_of_checks = fields.Integer(string="Number of checks", default=0, redonly=True)

    # New fields for two factor authentication
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

    # https://www.postgresql.org/docs/9.3/static/ddl-constraints.html
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', "FS Tokens must be unique!"),
    ]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fstoken_ids = fields.One2many(string='FS Partner Tokens', comodel_name='res.partner.fstoken',
                                  inverse_name='partner_id')


class FSTokenWizard(models.TransientModel):
    _name = 'res.partner.fstoken.wizard'

    expiration_date = fields.Date(string="Expiration Date", required=True,
                                  default=fields.datetime.now() + timedelta(days=14))

    @api.multi
    def set_expiration_date(self):
        # Get context
        ctx = self.env.context
        if not ctx:
            return {}
        if ctx.get('active_model') != 'res.partner.fstoken':
            raise Warning(_("Active model must be res.partner.fstoken!"))

        # Check expiration date set in wizard form view
        expiration_date = fields.datetime.strptime(self.expiration_date, "%Y-%m-%d")
        max_date = fields.datetime.now() + timedelta(weeks=30)

        if expiration_date > max_date:
            raise Warning(_("Expiration Date is not allowed to be more than 7 months (30 weeks) in the future!"))

        # Get res.parter.fstoken ids
        fstokens = self.env['res.partner.fstoken']
        if ctx.get('active_domain'):
            fstokens = fstokens.search(ctx['active_domain'])
        elif ctx.get('active_ids'):
            fstokens = fstokens.browse(ctx['active_ids'])

        # Set expiration_date for fstoken(s)
        if fstokens:
            fstokens.write({'expiration_date': self.expiration_date})

        # TODO: I think this should return True instead of a dict?
        return {}
