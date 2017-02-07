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
import time
import datetime


class AuthPartnerForm(http.Controller):

    @http.route(['/meine-daten', '/meinedaten'], auth='public', website=True)
    def index(self, **kwargs):
        partner = None
        apf_fields = list()
        field_errors = dict()
        errors_token = list()
        warnings_token = list()
        messages_token = list()
        errors = list()
        warnings = list()
        messages = list()
        fs_ptoken = kwargs.get('fs_ptoken')
        countries = None
        states = None

        # Honey Pot Field Test
        if kwargs.get('fs_hpf'):
            if request.uid != request.website.user_id.id:
                errors.append(_('Data found in field with label: "Do not enter data here please!"'))
            return http.request.render('auth_partner_form.meinedaten',
                                       {'kwargs': dict(),
                                        'fs_ptoken': '',
                                        'partner': '',
                                        'apf_fields': list(),
                                        'field_errors': dict(),
                                        'errors_token': errors_token,
                                        'warnings_token': warnings_token,
                                        'messages_token': messages_token,
                                        'errors': errors,
                                        'warnings': warnings,
                                        'messages': messages,
                                        'countries': None,
                                        'states': None,
                                        })

        # Check for fs_ptoken
        if fs_ptoken:
            # Sanitize fs_ptoken (remove all non alphanumeric characters and convert all chars to uppercase)
            fs_ptoken = ''.join(c.upper() for c in fs_ptoken.strip() if c.isalnum())
            # Find related res.partner for the token
            fstoken_obj = request.env['res.partner.fstoken']
            fstoken = fstoken_obj.sudo().search([('name', '=', fs_ptoken)], limit=1)
            # HINT: fstoken expiration_date is a mandatory field.
            if fstoken and fields.Datetime.from_string(fstoken.expiration_date) >= fields.datetime.now():
                # Valid Token was found!
                partner = fstoken.partner_id
                if len(kwargs) <= 2:
                    success_message = request.website.apf_token_success_message or _('Your code is valid!')
                    messages_token.append(success_message)

            # Wrong or expired token was given
            else:
                error_message = request.website.apf_token_error_message or _('Wrong or expired code!')
                errors_token.append(error_message)
                field_errors['fs_ptoken'] = 'fs_ptoken'

                # Add a delay of a second for every wrong try for the same session in the last 24h
                if request.session.get('wrong_token_date'):
                    # Reset if last incorrect try is older than 24h
                    if datetime.datetime.now() > request.session['wrong_token_date'] + datetime.timedelta(hours=24):
                        request.session['wrong_token_date'] = datetime.datetime.now()
                        request.session['wrong_token_tries'] = 1
                    else:
                        if request.session['wrong_token_tries'] > 3:
                            time.sleep(3)
                        request.session['wrong_token_tries'] += 1
                # This is the first wrong try so initialize "wrong_token_day" and "wrong_token_tries"
                else:
                    request.session['wrong_token_date'] = datetime.datetime.now()
                    request.session['wrong_token_tries'] = 1

                # TODO: Maybe add protection for new sessions spamming from the same ip?
                #       Problem: slow cause i need to store the ips in the database

        # Check for logged in user
        if request.uid != request.website.user_id.id:
            user_obj = request.env['res.users']
            user = user_obj.sudo().browse([request.uid])
            assert user.partner_id, _('You are logged in but your user has no res.partner assigned!')
            # Check if the res.partner of the logged in user matches the found partner by the fs_ptoken
            if partner and partner.id != user.partner_id.id:
                # HINT: This should never happen except the website is already called with a fs_ptoken in the url
                warnings.append(_('You are logged in but your login does not match the person for the given code! '
                                  'You will change the data for %s. '
                                  'If you want to change your data instead please clear the token code' % partner.name))
            else:
                partner = user.partner_id

        # Update the partner with the values from the from inputs
        # HINT: At this point a partner could only be found if the user had a valid code or a user is logged in
        if partner:

            # Check if the partner changed
            if request.session.get('apf_partner_id', partner.id) != partner.id:
                # partner has changed by login or new code: therefore reset kwargs except fs_ptoken
                kwargs = {'fs_ptoken': kwargs.get('fs_ptoken', '')}
            request.session['apf_partner_id'] = partner.id


            # Add countries and states
            countries = request.env['res.country']
            countries = countries.sudo().search([])
            states = request.env['res.country.state']
            states = states.sudo().search([])

            # Find fields_to_update
            # HINT: Since we know that either the token or the login is correct at this point the update is ok
            fields_to_update = dict()
            apf_fields = request.env['website.apf_partner_fields']
            apf_fields = apf_fields.sudo().search([])
            for field in apf_fields:
                if field.res_partner_field_id:
                    fname = field.res_partner_field_id.name
                    ftype = field.res_partner_field_id.ttype
                    # Search for field values  given by the form inputs
                    if fname in kwargs:
                        # NoData Fields can only be updated if there is something in the kwargs ELSE do NOT clear it!
                        if not field.nodata or field.nodata and kwargs[fname].strip() or ftype == 'boolean':
                            # Fix for Boolean fields: convert str() to boolean()
                            # HINT boolean field will ignore field.nodata setting
                            if ftype == 'boolean':
                                fields_to_update[fname] = True if kwargs[fname] else False
                            # Fix for Date fields: convert '' to None
                            elif ftype == 'date':
                                fields_to_update[fname] = kwargs[fname].strip() if kwargs[fname].strip() else None
                            else:
                                value = kwargs[fname].strip() if isinstance(kwargs[fname], basestring) else \
                                    kwargs[fname]
                                fields_to_update[fname] = value

            # Write to the res.partner (after field validation)
            # HINT: Only validate fields and write the partner if we found fields_to_update
            if fields_to_update:

                # VALIDATE FIELDS (before we update anything)
                # HINT: We do this here since fields_to_update indicates that something was entered in the
                #       Your Data section of the form. (= a partner was already found before)
                for field in apf_fields:
                    if field.res_partner_field_id:
                        fname = field.res_partner_field_id.name
                        ftype = field.res_partner_field_id.ttype
                        # Validate "mandatory" setting
                        if field.mandatory and not kwargs.get(fname):
                            field_errors[fname] = fname
                        # Validate date fields
                        if ftype == 'date' and kwargs[fname].strip():
                            date_de = kwargs[fname].strip()
                            try:
                                datetime.datetime.strptime(date_de, '%d.%m.%Y')
                            except:
                                field_errors[fname] = fname

                # Update res.partner (if no errors where found)
                if not field_errors:
                    # Add fstoken_update and fstoken_update_date
                    if fs_ptoken:
                        fields_to_update['fstoken_update'] = fs_ptoken
                        fields_to_update['fstoken_update_date'] = fields.datetime.now()
                    if partner.sudo().write(fields_to_update):
                        success_message = request.website.apf_update_success_message or \
                                          _('Your data was successfully updated!')
                        messages.append(success_message)
                    else:
                        warnings.append(_('Your data could not be updated. Please try again.'))

            # Add error message for field_errors
            if field_errors:
                errors.append(_('Missing or incorrect information! Please check your input.'))

        # HINT: use kwargs.get('fs_ptoken', '') to get the format of the website corrected by java script
        return http.request.render('auth_partner_form.meinedaten',
                                   {'kwargs': kwargs,
                                    'fs_ptoken': kwargs.get('fs_ptoken', ''),
                                    'partner': partner,
                                    'apf_fields': apf_fields,
                                    'field_errors': field_errors,
                                    'errors_token': errors_token,
                                    'warnings_token': warnings_token,
                                    'messages_token': messages_token,
                                    'errors': errors,
                                    'warnings': warnings,
                                    'messages': messages,
                                    'countries': countries,
                                    'states': states,
                                    })
