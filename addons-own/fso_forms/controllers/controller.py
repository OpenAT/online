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
from openerp.tools.translate import _

# import locale
# import urllib2
import base64
import datetime

import logging
_logger = logging.getLogger(__name__)


class FsoForms(http.Controller):

    # Allowed and necessary keys for a fso_form in request.session
    _valid_form_sdata_keys = ('form_id', 'form_uid', 'form_record_id', 'form_model_id',
                              'clear_session_data')

    def get_fso_form_session_key(self, form_id):
        assert form_id and int(form_id), "FSO Form ID must be a valid integer!"
        return 'fso_form_' + str(form_id)

    # ATTENTION: !!! request.session information will be copied between multiple request but
    #                NOT DEEP copied! Therefore never use nested data structures in request.session!
    def set_fso_form_session_data(self, form_id, form_uid, form_record_id, form_model_id,
                                  clear_session_data=False):
        form_id = str(form_id)
        form_key = self.get_fso_form_session_key(form_id)

        # Store / Overwrite the form information in the current session
        request.session[form_key] = {
            'form_id': form_id,
            'form_uid': form_uid,
            'form_record_id': form_record_id,
            'form_model_id': form_model_id,
            'clear_session_data': clear_session_data,
        }

    def get_fso_form_session_data(self, form, check_clear_session_data=True):
        """
        Returns the session data of the form if the data still matches the current form data and request user

        :param form_id:
        :param check_clear_session_data:
        :return:
        """
        form_id = str(form.id)
        form_key = self.get_fso_form_session_key(form_id)

        # Get form session data
        form_sdata = request.session.get(form_key, False)

        # Return an empty dict if there is no session data at all
        if not form_sdata:
            _logger.info("No fso form session data found for form_id %s" % form_id)
            return dict()

        # Check the structure of the form session data
        form_sdata_keys = form_sdata.keys()
        if not isinstance(form_sdata, dict) or set(form_sdata_keys) != set(self._valid_form_sdata_keys):
            _logger.error('Remove fso_form %s session data because of unexpected or missing keys in %s!'
                          '' % (form_id, str(form_sdata_keys)))
            self.remove_fso_form_session_data(form_id)
            return dict()

        # Check if the user changed (e.g. after an login or logout)
        if request.uid != form_sdata['form_uid']:
            self.remove_fso_form_session_data(form_id)
            return dict()

        # Check if the form model changed
        if form.model_id.id != form_sdata['form_model_id']:
            self.remove_fso_form_session_data(form_id)
            return dict()

        # Check if we need to clear the form session data anyway
        if check_clear_session_data:
            if form_sdata['clear_session_data']:
                self.remove_fso_form_session_data(form_id)
                return dict()

        # Return the form session data
        return form_sdata

    def remove_fso_form_session_data(self, form_id):
        form_id = str(form_id)
        form_key = self.get_fso_form_session_key(form_id)
        # Remove the form session data
        request.session.pop(form_key, False)

    def get_fso_form_records_by_user(self, form=None, user=None):
        """
        Return all records of the form model (form.model_id.model) where the login-marked-field of the form model
        matches the given user or it's related partner!

        Inherit this method if you need to choose a specific record out of the found records. (e.g. status=approved)

        :param form: The fso form record
        :param user: The logged in user record
        :return: recordset of the form model
        """
        form_model_name = form.model_id.model

        # TODO: Replace sudo with the logged in user or by users set in the form to write the record
        form_model_obj = request.env[form_model_name].sudo()

        if form_model_name == 'res.user':
            return user
        if form_model_name == 'res.partner':
            return user.partner_id

        # Try to find a 'login' field in the current form
        login_field = form.field_ids.filtered(lambda r: r.login)
        if not login_field or len(login_field) != 1 or login_field.field_id.related not in ['res.user', 'res.partner']:
            return form_model_obj

        # Search for all records in the form-model where the login field matches the currently logged in user or
        # its related partner
        search_id = user.id if login_field.field_id.related == 'res.user' else user.partner_id.id
        records = form_model_obj.search([(login_field.field_id.name, '=', search_id)])
        if not records:
            return form_model_obj

        return records

    def get_fso_form_record(self, form):
        """
        Search
        :param form: The form recordset.ensureone()
        :return: recordset of the form model (one record or empty recordset!)
        """
        form_model_name = form.model_id.model

        # TODO: Replace sudo with the logged in user or by users set in the form to write the record
        form_model_obj = request.env[form_model_name].sudo()

        # Get the request user if the current user is not the website public user
        logged_in_user = False
        if request.website.user_id.id != request.uid:
            logged_in_user = request.env['res.users'].sudo().browse([request.uid])

        # A) TRY TO FIND A FORM-RELATED-RECORD BASED ON THE LOGGED IN USER AND THE LOGIN-MARKED-FIELD
        # -------------------------------------------------------------------------------------------
        # HINT: Only if 'edit_existing_record_if_logged_in' is set in the form!
        if logged_in_user and form.edit_existing_record_if_logged_in:

            # HINT: You may inherit get_fso_form_records_by_user() to select or filter for a different record!
            form_records_by_user = self.get_fso_form_records_by_user(form=form, user=logged_in_user)

            # Return a record only if exactly ONE record was found
            # Record found
            if form_records_by_user and len(form_records_by_user) == 1:
                record_by_user = form_records_by_user

                # Set/Update the session data based on the found record but without clear session data since
                # 'edit_existing_record_if_logged_in' is set!
                self.set_fso_form_session_data(form_id=form.id,
                                               form_uid=logged_in_user.id,
                                               form_record_id=record_by_user.id,
                                               form_model_id=form.model_id.id,
                                               clear_session_data=False)

                # Return the record
                return form_records_by_user

            # Record was not found
            else:
                return form_model_obj

        # B) TRY TO FIND THE RECORD BASED ON THE CURRENT SESSION
        # ------------------------------------------------------
        form_sdata = self.get_fso_form_session_data(form)
        if not form_sdata:
            return form_model_obj
        record = form_model_obj.sudo().browse([form_sdata['form_record_id']])
        # Record not found
        if len(record) != 1:
            _logger.error('Fso form record stored in session data not found! Removing form data from session!')
            self.remove_fso_form_session_data(form.id)
            return form_model_obj
        # Record found
        return record

    def validate_fields(self, form, field_data):
        field_errors = dict()
        for f in form.field_ids:

            if f.field_id and f.show:

                # ATTENTION: Skipp readonly fields if a user is logged in
                if f.readonly and request.website.user_id.id != request.uid:
                    continue

                f_name = f.field_id.name
                f_display_name = f.label if f.label else f_name
                f_type = f.field_id.ttype
                f_style = f.style

                # Get the value of the field
                if f_type == 'boolean':
                    if f_style == 'radio':
                        f_value = True if field_data.get(f_name, None) == 'True' else False
                    else:
                        f_value = True if field_data.get(f_name, None) else False
                else:
                    if f_style in ['radio', 'radio_selectnone']:
                        f_value = field_data.get(f_name, False)
                    else:
                        f_value = field_data[f_name]

                # Mandatory
                if f.mandatory and not f_value:
                    field_errors[f_name] = _("No value for mandatory field %s" % f_display_name)
                    continue

                # Date format
                # TODO: Localization !!!
                if f.field_id.ttype == 'date' and f_value:
                    try:
                        datetime.datetime.strptime(f_value.strip(), '%d.%m.%Y')
                    except Exception as e:
                        _logger.warning('Date conversion failed for string %s' % f_value)
                        field_errors[f_name] = _("Please enter a valid date for field %s" % f_display_name)
                        continue

                # Integers
                if f.field_id.ttype == 'integer' and f_value:
                    try:
                        int(f_value)
                    except Exception as e:
                        _logger.warning('Integer conversion failed for string %s' % f_value)
                        field_errors[f_name] = _("Please enter a valid number for field %s" % f_display_name)
                        continue

                # Floats
                # TODO: Localization - !!! Right now we always expect DE values e.g.: 22.000,12 !!!
                if f.field_id.ttype == 'float' and f_value:
                    try:
                        # Clean up and convert DE Float-Strings
                        assert len(f_value.rsplit(',')[-1]) <= len(f_value.rsplit('.')[-1]), 'Wrong float format?!?'
                        float(f_value.replace(',', ':').replace('.', '').replace(':', '.'))
                    except Exception as e:
                        _logger.warning('Float conversion failed for string %s' % f_value)
                        field_errors[f_name] = _("Please enter a valid float for field %s" % f_display_name)
                        continue

                # TODO: validate binary (mime type)

        return field_errors

    def _prepare_field_data(self, form=None, form_field_data=None):
        form_field_data = form_field_data or {}

        # Transform the form field data if needed
        values = {}

        # Loop through all the fields in the form
        for f in form.field_ids:
            if f.field_id and f.show:

                # ATTENTION: Skipp readonly fields if a user is logged in
                if f.readonly and request.website.user_id.id != request.uid:
                    continue

                f_name = f.field_id.name
                f_type = f.field_id.ttype
                f_style = f.style

                # Get the value of the field
                if f_type == 'boolean':
                    if f_style == 'radio':
                        f_value = True if form_field_data.get(f_name, None) == 'True' else False
                    else:
                        f_value = True if form_field_data.get(f_name, None) else False
                else:
                    if f_style in ['radio', 'radio_selectnone']:
                        f_value = form_field_data.get(f_name, False)
                    else:
                        f_value = form_field_data[f_name]

                # Skipp NODATA fields if empty or False
                # HINT: Fields with no pre-filled data (nodata) can only be included if there is a value in field_data
                #       Otherwise we may clear the existing value by accident!
                if f.nodata and not f_value:
                    continue

                # Add BOOLEAN
                if f_type == 'boolean':
                    values[f_name] = True if f_value else False

                # Add DATE
                elif f_type == 'date':
                    if f_value:
                        # TODO: Localization !!!
                        f_value = datetime.datetime.strptime(f_value.strip(), '%d.%m.%Y')
                    values[f_name] = f_value or False

                # Add BINARY
                elif f_type == 'binary':
                    if f_value:
                        values[f_name] = base64.encodestring(f_value.read()) or False
                        if f.binary_name_field_id:
                            values[f.binary_name_field_id.name] = f_value.filename if values[f_name] else False
                    else:
                        values[f_name] = False
                        if f.binary_name_field_id:
                            values[f.binary_name_field_id.name] = False

                # Add FLOAT
                # TODO: Localization - !!! Right now we expect DE values from the forms !!!
                elif f_type == 'float':
                    if f_value:
                        values[f_name] = f_value.replace(',', ':').replace('.', '').replace(':', '.')

                # Add OTHER FIELD TYPES
                else:
                    values[f_name] = f_value or False

        return values

    def _prepare_kwargs_for_form(self, form, **kwargs):
        # Remove binary fields (e.g. images) from kwargs before rendering the form
        # TODO: This will be disabled in the future since we need to 'show' the images for GL2K Nationalparkgarten!
        if kwargs:
            for f in form.field_ids:
                if f.field_id and f.field_id.ttype == 'binary':
                    if f.field_id.name in kwargs:
                        kwargs.pop(f.field_id.name)
        return kwargs

    @http.route(['/fso/form/<int:form_id>'], methods=['POST', 'GET'], type='http', auth="public", website=True)
    def fso_form(self, form_id=False, **kwargs):
        form_id = int(form_id)
        form = request.env['fson.form'].sudo().browse([form_id])
        if len(form) != 1:
            _logger.error('Form with id %s not found! Redirecting to startpage!' % str(form_id))
            return request.redirect("/")

        # Initialize the frontend message lists
        errors = list()
        warnings = list()
        messages = list()
        form_field_errors = dict()

        # Get the form and session related record
        # HINT: This will either return a single record or an empty recordset (= form.model_id.model object)
        # HINT: The recordset user is always sudo() right now! :(
        #       TODO: add user fields to form for security restrictions
        # TODO: If 'edit_existing_record_if_logged_in' is set in the form there is no way right now to create a new
        #       record - which is just what we want since we expect one and only one record per form for this logged
        #       in user. BUT if we once expand the generator for more than one record we need to find a mechanism
        #       To allow this in the form - maybe a "Create new record" button
        record = self.get_fso_form_record(form)

        # HANDLE FORM SUBMISSION
        # ----------------------
        if kwargs and request.httprequest.method == 'POST':
            logging.info("FSO FORM SUBMIT: %s" % kwargs)

            # Validate Fields before we create or update a record
            form_field_errors = self.validate_fields(form, field_data=kwargs)
            warnings += ['"%s": %s' % (kwargs.get(f, f), msg) for f, msg in form_field_errors.iteritems()]

            if not warnings and not errors:
                # Create or Update the record
                # HINT: User rights are handled by get_fso_form_record() ...  always sudo() right now :(
                values = self._prepare_field_data(form=form, form_field_data=kwargs)
                if values:
                    try:
                        if not record:
                            record = record.create(values)
                            messages.append(_('Data was successfully submitted!'))
                        else:
                            record.write(values)
                            messages.append(_('Data was successfully updated!'))
                        # Update the session data
                        # HINT: If clear_session_data_after_submit is set the form will be empty at the next hit/load!
                        #       This has no effect if a user is logged in and 'edit_existing_record_if_logged_in' is
                        #       also set! In that case get_fso_form_record() will overwrite the session data set here
                        #       and set 'clear_session_data' to False in the method get_fso_form_record() !
                        self.set_fso_form_session_data(form_id=form.id,
                                                       form_uid=request.uid,
                                                       form_record_id=record.id,
                                                       form_model_id=form.model_id.id,
                                                       clear_session_data=form.clear_session_data_after_submit)
                    except Exception as e:
                        errors.append(_('Submission failed!\n\n%s' % repr(e)))
                        pass

                # Redirect to Thank you Page if set by the form
                # HINT: This is the only page where you could edit the data again if not logged in by pressing the
                #       edit button
                if form.thank_you_page_after_submit and not warnings and not errors:
                    # request.session['mikes_test'] = {'a': 1, 'b': {'c': 'form'}}
                    return request.redirect("/fso/form/thanks/"+str(form.id))

        # FINALLY RENDER THE FORM
        # -----------------------
        return http.request.render('fso_forms.form',
                                   {'kwargs': self._prepare_kwargs_for_form(form, **kwargs),
                                    # Form record
                                    'form': form,
                                    # Set error css-classes to the field-form-groups
                                    'form_field_errors': form_field_errors,
                                    # Record created by the form
                                    'record': record,
                                    # Messages
                                    'errors': errors,
                                    'warnings': warnings,
                                    'messages': messages,
                                    })

    @http.route(['/fso/form/thanks/<int:form_id>'], methods=['POST', 'GET'], type='http', auth="public", website=True)
    def fso_form_thanks(self, form_id=False, **kwargs):
        form_id = int(form_id)

        # Get Form
        # ATTENTION: Always use a list for browse()
        form = request.env['fson.form'].browse([form_id])
        if not form:
            _logger.error('Form with id %s not found! Redirecting to startpage!' % str(form_id))
            return request.redirect("/")

        # FORM SUBMIT FOR EDIT BUTTON
        # TODO: Right now this is a simple get request from an <a></a>
        #       We should add a UUID im the session data and submit a form by the edit button with a hidden input field
        #       containing the guid - it may be safer than just depend on the form data in the session - but im not
        #       sure about that since an attacker that will call /fso/form/[n]?edit_form_data=True would still have
        #       no form data in the memory on the server.
        if kwargs.get('edit_form_data', False):
            # Set 'clear_session_data' to False before we redirect to the form again
            form_sdata = self.get_fso_form_session_data(form, check_clear_session_data=False)
            if form_sdata:
                self.set_fso_form_session_data(form.id,
                                               form_sdata['form_uid'],
                                               form_sdata['form_record_id'],
                                               form_sdata['form_model_id'],
                                               clear_session_data=False)
            return request.redirect("/fso/form/"+str(form.id))

        # Render the thanks template
        return http.request.render('fso_forms.thanks',
                                   {'kwargs': kwargs,
                                    # form
                                    'form': form})
