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

from openerp import http
from openerp.http import request
from openerp import fields
from openerp.tools.translate import _


class AuthPartnerForm(http.Controller):

    @http.route(['/meine-daten/', '/meinedaten/'], auth='public', website=True)
    def index(self, **kwargs):
        partner = None
        apf_fields = list()
        field_errors = dict()
        errors = list()
        warnings = list()
        messages = list()
        fs_ptoken = kwargs.get('fs_ptoken')

        # Check for fs_ptoken
        if fs_ptoken:
            # Sanitize fs_ptoken (remove all non alphanumeric characters and convert all chars to uppercase)
            fs_ptoken = ''.join(c.upper() for c in fs_ptoken if c.isalnum())
            # Find related res.partner for the token
            fstoken_obj = request.env['res.partner.fstoken']
            fstoken = fstoken_obj.sudo().search([('name', '=', fs_ptoken)], limit=1)
            # HINT: fstoken expiration_date is a mandatory field.
            if fstoken and fields.Datetime.from_string(fstoken.expiration_date) >= fields.datetime.now():
                # Valid Token was found!
                partner = fstoken.partner_id
                messages += _('Code is valid!')
            else:
                # Token was given but not valid!
                # TODO: Add a waiting time and expand it with every wrong try
                errors += 'Wrong or expired code!'

        # Check for logged in user
        if request.uid != request.website.user_id.id:
            user_obj = request.env['res.users']
            user = user_obj.sudo().browse([request.uid])
            assert user.partner_id, _('You are logged in but your user has no res.partner assigned!')
            # Check if the res.partner of the logged in user matches the found partner by the fs_ptoken
            if partner and partner.id != user.partner_id.id:
                # HINT: This should never happen except the website is already called with a fs_ptoken in the url
                warnings += _('You are logged in but your login does not match the person for the given code! '
                              'You will change the data for %s. '
                              'If you want to change your data instead please press the reset button.' % partner.name)
            else:
                partner = user.partner_id

        # Update the partner with the values from the from inputs
        if partner:
            apf_fields = request.env['website.apf_partner_fields']
            apf_fields = apf_fields.sudo().search([])
            fields_to_update = dict()

            # Update the res.partner with the values from kwargs if any
            # HINT: Since we know that either the token or the login is correct at this point the update is ok
            for field in apf_fields:
                fname = field.res_partner_field_id.name
                ftype = field.res_partner_field_id.ttype
                # TODO: Do some field validation (e.g. Mandatory, Format, ...)
                # TODO: Add a honeypot field
                # Search for field values  given by the form inputs
                if fname in kwargs:
                    # Fix for Boolean fields: convert str() to boolean()
                    if ftype == 'boolean':
                        fields_to_update[fname] = True if kwargs[fname] else False
                    else:
                        fields_to_update[fname] = kwargs[fname]
            # If we found any fields update the res.partner now
            if fields_to_update:
                partner.sudo().write(fields_to_update)

        # Add countries and states
        countries = request.env['res.country']
        countries = countries.sudo().search([])
        states = request.env['res.country.state']
        states = states.sudo().search([])

        return http.request.render('auth_partner_form.meinedaten',
                                   {'kwargs': kwargs,
                                    'fs_ptoken': kwargs.get('fs_ptoken'),
                                    'partner': partner,
                                    'apf_fields': apf_fields,
                                    'field_errors': field_errors,
                                    'errors': errors,
                                    'warnings': warnings,
                                    'messages': messages,
                                    'countries': countries,
                                    'states': states,
                                    })
