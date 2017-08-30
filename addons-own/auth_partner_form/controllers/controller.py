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
from openerp.addons.auth_partner.fstoken_tools import fstoken_check
from openerp.addons.web.controllers.main import login_and_redirect

import urllib2
import datetime
import logging
_logger = logging.getLogger(__name__)


class AuthPartnerForm(http.Controller):

    @http.route(['/meine-daten', '/meinedaten'], auth='public', website=True)
    def meine_daten(self, **kwargs):
        # Token related
        fstoken = kwargs.get('fstoken')
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

        # CHECK TOKEN AND LOGIN
        token_record = None
        if fstoken:
            # Check token
            token_record, token_user, token_error = fstoken_check(fstoken)

            # Valid token (= Valid res.partner and valid res.user)
            if token_record:
                # Login if token res.user is different from request user
                if token_user and token_user.id != request.uid:
                    redirect_url = '/meine-daten?fstoken=' + urllib2.quote(fstoken)
                    _logger.info('Login by /meine-daten FS-Token input (%s): user.login %s (%s) and redirect to %s'
                                 % (token_record.id, token_user.login, token_user.id, redirect_url))
                    return login_and_redirect(request.db, token_user.login, token_record.name,
                                              redirect_url=redirect_url)
            # Wrong or invalid token
            if token_error:
                field_errors['fstoken'] = fstoken
                # Check if a custom message was set for the token error message
                # or use the standard error message from fstoken_check
                try:
                    if request.website.apf_token_error_message and len(request.website.apf_token_error_message) > 2:
                        errors_token += [request.website.apf_token_error_message]
                    else:
                        errors_token += token_error
                except:
                    errors_token += token_error

        # UPDATE PARTNER
        # HINT: Only if logged in (so different from the default user request.website.user_id)
        if request.website.user_id.id != request.uid:
            _logger.debug('/meine-daten request.website.user_id %s, request.uid %s'
                         % (request.website.user_id, request.uid))
            user = request.env['res.users'].sudo().browse([request.uid])
            partner = user.partner_id

            # Add countries and states
            countries = request.env['res.country']
            countries = countries.sudo().search([])
            states = request.env['res.country.state']
            states = states.sudo().search([])

            # Find fields_to_update
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
                                if fields_to_update[fname]:
                                    # Convert Date from %d.%m.%Y to %Y-%m-%d
                                    # HINT: In the meine-daten form only a date-format %d.%m.%Y is allowed!
                                    #       Language settings of odoo are not taken into account! Therefore we must
                                    #       Convert the date string from the website to a datetime here with the correct
                                    #       format.
                                    fields_to_update[fname] = fields.datetime.strptime(fields_to_update[fname],
                                                                                       '%d.%m.%Y')
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
                    #                      function fstoken_check()
                    if fstoken:
                        fields_to_update['fstoken_update'] = fstoken
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

        # Show a token success message after login but before the first partner data form submission
        if token_record and fstoken and len(kwargs) <= 2:
            token_valid_message = request.website.apf_token_success_message or _('Your code is valid!')
            messages_token.append(token_valid_message)

        return http.request.render('auth_partner_form.meinedaten',
                                   {'kwargs': kwargs,
                                    'fstoken': fstoken,
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

    @http.route(['/check_bpk'], type='json', auth='user', website=True)
    def check_bpk(self, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context

        firstname = kwargs.get('firstname', '')
        lastname = kwargs.get('lastname', '')
        birthdate = kwargs.get('birthdate', '')

        partner_obj = request.registry['res.partner']
        bpk_ok = partner_obj.check_bpk(cr, uid, firstname=firstname, lastname=lastname, birthdate=birthdate)

        return bpk_ok
