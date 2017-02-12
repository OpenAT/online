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
import datetime
from openerp.addons.auth_partner.fstoken_tools import fstoken


class AuthPartnerForm(http.Controller):

    @http.route(['/meine-daten', '/meinedaten'], auth='public', website=True)
    def index(self, **kwargs):
        # Token related
        fs_ptoken = kwargs.get('fs_ptoken')
        partner = None
        messages_token = list()
        warnings_token = list()
        errors_token = list()
        # Form related
        apf_fields = list()
        field_errors = dict()
        messages = list()
        warnings = list()
        errors = list()
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

        # CHECK FSTOKEN
        # HINT: if fs_ptoken=False fstoken() will search for a valid token in the session
        partner, messages_token, warnings_token, errors_token = fstoken(fs_ptoken=fs_ptoken)

        # UPDATE PARTNER
        # Update the partner with the values from the form input fields
        # HINT: At this point a partner could only be found if the user had a valid code or a user is logged in
        if partner:

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
                    # DEPRECATION WARNING! This is only here for the auth_partner_form and was
                    #                      replaced by field "last_date_of_use" in "res.partner.fstoken" in the
                    #                      function fs_ptoken()
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
        # HINT: Show only messages_token if the form is not submitting res.parnter field data from the form
        messages_token = messages_token if kwargs.get('fs_ptoken') and 'lastname' not in kwargs else list()
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
