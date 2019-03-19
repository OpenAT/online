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

import locale
import urllib2
import base64
import datetime
import logging
_logger = logging.getLogger(__name__)


class FsoForms(http.Controller):

    # TODO: Set and get only data for one form not forms! and add a rem_fso_form_session_data(form_id) method !!!
    def get_fso_forms_session_data(self):
        # Cleanup in case something went wrong and fso_forms is still in session but no dict
        if not isinstance(request.session.get('fso_forms', dict()), dict):
            request.session.pop('fso_forms')

        fso_forms_session_data = dict()
        if hasattr(request, 'session'):
            fso_forms_session_data = request.session.get('fso_forms', dict())

        # Cleanup if data is missing! e.g.: On structural change of the dict!
        if fso_forms_session_data:
            for form_id, form_vals_dict in fso_forms_session_data.iteritems():
                if not all(keys in list(form_vals_dict.keys())
                           for keys in ('form_uid', 'form_record_id','form_model_id')):
                    _logger.error('Key missing in form_vals_dict')
                    request.session.pop('fso_forms')
                    fso_forms_session_data = dict()
                    break

        return fso_forms_session_data

    def set_fso_forms_session_data(self, form_id, form_user_id, form_record_id, form_model_id):
        assert hasattr(request, 'session'), 'Current request has no session attribute!'
        fso_forms_session_data = self.get_fso_forms_session_data()
        fso_forms_session_data.update({form_id: {'form_uid': form_user_id,
                                                 'form_record_id': form_record_id,
                                                 'form_model_id': form_model_id}
                                       })
        request.session['fso_forms'] = fso_forms_session_data
        return True

    def get_record(self, form):
        # Get fso_form session data
        fso_forms_session_data = self.get_fso_forms_session_data()
        form_session_data = fso_forms_session_data.get(form.id, False) if fso_forms_session_data else False

        # No session data for this form
        if not fso_forms_session_data or not form_session_data:
            return request.env[form.model_id.model]

        # User changed
        if form_session_data['form_uid'] != request.uid:
            # TODO: Check if this removes it in request.session too
            fso_forms_session_data.pop(form.id)
            _logger.warning('Form user changed!')
            return request.env[form.model_id.model]

        # Form model changed
        if form_session_data['form_model_id'] != form.model_id.id:
            # TODO: Check if this removes it in request.session too
            fso_forms_session_data.pop(form.id)
            _logger.warning('Form model changed!')
            return request.env[form.model_id.model]

        # Return the record
        return request.env[form.model_id.model].browse([form_session_data['form_record_id']])

    # TODO: Maybe we need to move this to the model?!? right now an exception on write kills the rendering ?!?
    def update_record(self, form, field_data):
        # Prepare values
        values = {}
        for f in form.field_ids:
            if f.field_id and f.show:
                f_name = f.field_id.name
                f_type = f.field_id.ttype
                # HINT: Boolean fields would not be in 'field_data' if not checked in the form
                f_value = field_data.get(f_name, False) if f_type == 'boolean' else field_data[f_name]

                # NODATA
                # Fields with no pre-filled data (nodata) can only be included if there is a value in field_data to not
                # clear them accidentally!
                if f.nodata and not f_value:
                    continue

                # BOOLEAN TYPE
                if f_type == 'boolean':
                    values[f_name] = True if f_value else False

                # DATE TYPE
                elif f_type == 'date':
                    if f_value:
                        # TODO: Localization
                        f_value = datetime.datetime.strptime(f_value.strip(), '%d.%m.%Y')
                    values[f_name] = f_value or False

                # BINARY TYPE
                elif f_type == 'binary':
                    if f_value:
                        values[f_name] = base64.encodestring(f_value.read()) or False
                        if f.binary_name_field_id:
                            values[f.binary_name_field_id.name] = f_value.filename if values[f_name] else False
                    else:
                        values[f_name] = False
                        if f.binary_name_field_id:
                            values[f.binary_name_field_id.name] = False

                # FLOAT TYPE
                # TODO: Localization - !!! Right now we expect DE values from the forms !!!
                elif f_type == 'float':
                    if f_value:
                        values[f_name] = f_value.replace(',', ':').replace('.', '').replace(':', '.')

                # ALL OTHER FIELD TYPES
                else:
                    values[f_name] = f_value or False

        # Get current record if any
        # HINT: get_record() will handle user changes and model changes so no need to do it here again
        record = self.get_record(form)

        # Return the record if no values are there to update
        if not values:
            _logger.warning('No values to update! Returning record without update!')
            return record

        # Update or create the record
        if record:
            record.write(values)
        else:
            record = request.env[form.model_id.model].create(values)

        # Update the session data
        self.set_fso_forms_session_data(form_id=form.id, form_user_id=request.uid, form_record_id=record.id,
                                        form_model_id=form.model_id.id)

        # Return the created or updated record
        return record

    def validate_fields(self, form, field_data):
        field_errors = dict()
        for f in form.field_ids:

            if f.field_id and f.show:
                f_name = f.field_id.name
                f_type = f.field_id.ttype
                # HINT: Boolean fields would not be in 'field_data' if not checked in the form
                f_value = field_data.get(f_name, False) if f_type == 'boolean' else field_data[f_name]
                f_display_name = f.label if f.label else f_name

                # Check mandatory setting
                if f.mandatory and not f_value:
                    field_errors[f_name] = _("No value for mandatory field %s" % f_display_name)
                    continue

                # Check date format
                # TODO: Localization
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
                # TODO: Localization - !!! Right now we alwys expect DE values from the forms e.g.: 22.000,12 !!!
                if f.field_id.ttype == 'float' and f_value:
                    try:
                        assert len(f_value.rsplit(',')[-1]) <= len(f_value.rsplit('.')[-1]), 'Wrong float format?!?'
                        float(f_value.replace(',', ':').replace('.', '').replace(':', '.'))
                    except Exception as e:
                        _logger.warning('Float conversion failed for string %s' % f_value)
                        field_errors[f_name] = _("Please enter a valid float for field %s" % f_display_name)
                        continue

                # TODO: validate binary

        return field_errors

    @http.route(['/fso/form/<int:form_id>'], methods=['POST', 'GET'], type='http', auth="public", website=True)
    def fso_form(self, form_id=False, **kwargs):
        form_id = int(form_id) if form_id else form_id

        errors = list()
        warnings = list()
        messages = list()

        form_field_errors = dict()

        # Get Form
        # ATTENTION: Always use a list for browse()
        form = request.env['fson.form'].browse([form_id])
        if not form:
            _logger.error('Form with id %s not found! Redirecting to startpage!' % str(form_id))
            return request.redirect("/")

        # Get Record from session data if one exits already and the user has not changed!
        record = self.get_record(form)

        # FORM SUBMIT
        if kwargs and request.httprequest.method == 'POST':
            logging.info("FORM SUBMIT: %s" % kwargs)

            # Validate Fields
            form_field_errors = self.validate_fields(form, field_data=kwargs)
            if form_field_errors:
                return http.request.render('fso_forms.form',
                                           {'kwargs': kwargs,
                                            'form': form,
                                            'form_field_errors': form_field_errors,
                                            'record': record,
                                            'errors': errors,
                                            'warnings': warnings,
                                            'messages': messages,
                                            })

            # Create or update the record and the session data
            try:
                new_record = self.update_record(form, field_data=kwargs)
                if new_record == record:
                    messages.append(_('Data was successfully updated!'))
                else:
                    messages.append(_('Data was successfully submitted!'))
                record = new_record
            except Exception as e:
                warnings.append(_('Update of Record failed!\n%s' % repr(e)))

        # Remove binary fields from kwargs before rendering the form
        if kwargs:
            for f in form.field_ids:
                if f.field_id and f.field_id.ttype == 'binary':
                    if f.field_id.name in kwargs:
                        kwargs.pop(f.field_id.name)

        # Render the template
        return http.request.render('fso_forms.form',
                                   {'kwargs': kwargs,
                                    # form
                                    'form': form,
                                    'form_field_errors': form_field_errors,
                                    # Record created by the form or partner if model is res.partner and logged in
                                    'record': record,
                                    # Messages
                                    'errors': errors,
                                    'warnings': warnings,
                                    'messages': messages,
                                    })

