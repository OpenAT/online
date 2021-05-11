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
from openerp.tools.translate import _
from openerp.exceptions import Warning


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
