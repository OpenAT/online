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

#import locale
#import urllib2
import base64
import datetime
import logging
_logger = logging.getLogger(__name__)


class FsoForms(http.Controller):

    _valid_form_sdata_keys = ('form_uid', 'form_record_id', 'form_model_id', 'clear_session_data')

    # ATTENTION: request.session information will be copied but not DEEP copied so only use flat dicts!

    def get_fso_form_session_data(self, form_id, check_clear_session_data=True):
        if form_id:
            form_id = str(form_id)

        form_key = 'fso_form_' + form_id

        # Get form session data
        form_sdata = request.session.get(form_key, False)
        if not form_sdata:
            form_sdata = dict()
            return form_sdata

        # Check keys
        form_sdata_keys = form_sdata.keys()
        if not isinstance(form_sdata, dict) or set(form_sdata_keys) != set(self._valid_form_sdata_keys):
            _logger.error('Remove fso_form %s session data because of unexpected or missing keys in %s!'
                          '' % (form_id, str(form_sdata_keys)))
            request.session.pop(form_key)
            form_sdata = dict()
            return form_sdata

        # Check clear_session_data
        if check_clear_session_data:
            if form_sdata['clear_session_data']:
                request.session.pop(form_key)
                form_sdata = dict()
                return form_sdata

        # Return the form session data
        return form_sdata

    def set_fso_form_session_data(self, form_id, form_uid, form_record_id, form_model_id, clear_session_data=False):
        if form_id:
            form_id = str(form_id)

        form_key = 'fso_form_' + form_id

        # Overwrite or create the form session data
        request.session[form_key] = {
            'form_uid': form_uid,
            'form_record_id': form_record_id,
            'form_model_id': form_model_id,
            'clear_session_data': clear_session_data
        }

    def pop_fso_form_session_data(self, form_id):
        if form_id:
            form_id = str(form_id)

        form_key = 'fso_form_' + form_id

        request.session.pop(form_key, False)

    def get_record(self, form):
        form_sdata = self.get_fso_form_session_data(form.id)

        # No session data for this form
        if not form_sdata:
            return request.env[form.model_id.model]

        # User changed
        if form_sdata['form_uid'] != request.uid:
            self.pop_fso_form_session_data(form.id)
            _logger.warning('Form user changed!')
            return request.env[form.model_id.model]

        # Form model changed
        if form_sdata['form_model_id'] != form.model_id.id:
            self.pop_fso_form_session_data(form.id)
            _logger.warning('Form model changed!')
            return request.env[form.model_id.model]

        # Return the record
        record = request.env[form.model_id.model].browse([form_sdata['form_record_id']])
        return record

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
            # TODO: Remove sudo() for record creation and add special fields in form to set access for record creation
            record.sudo().write(values)
        else:
            # TODO: Remove sudo() for record creation and add special fields in form to set access for record creation
            record = request.env[form.model_id.model].sudo().create(values)

        # Update the session data and set clear_session_data
        # ATTENTION: !!! If clear_session_data is True the data will be removed by get_fso_form_session_data() !!!
        self.set_fso_form_session_data(form_id=form.id, form_uid=request.uid, form_record_id=record.id,
                                       form_model_id=form.model_id.id,
                                       clear_session_data=form.clear_session_data_after_submit)

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
                # TODO: Localization - !!! Right now we always expect DE values e.g.: 22.000,12 !!!
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
        ses = request.session
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

        # Get Record FROM FORM SESSION_DATA
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

            # Create or update the record AND THE FORM_SESSION_DATA
            try:
                new_record = self.update_record(form, field_data=kwargs)
                if new_record == record:
                    messages.append(_('Data was successfully updated!'))
                else:
                    messages.append(_('Data was successfully submitted!'))
                record = new_record
            except Exception as e:
                warnings.append(_('Update of Record failed!\n\n%s' % repr(e)))

            # Redirect to Thank you Page
            if form.thank_you_page_after_submit and not form_field_errors and not warnings and not errors:
                request.session['mikes_test'] = {'a': 1, 'b': {'c': 'form'}}
                return request.redirect("/fso/form/thanks/"+str(form.id))
                # return http.request.render('fso_forms.thanks',
                #                            {'kwargs': kwargs,
                #                             # form
                #                             'form': form})

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

    @http.route(['/fso/form/thanks/<int:form_id>'], methods=['POST', 'GET'], type='http', auth="public", website=True)
    def fso_form_thanks(self, form_id=False, **kwargs):
        ses = request.session
        form_id = int(form_id) if form_id else form_id

        # Get Form
        # ATTENTION: Always use a list for browse()
        form = request.env['fson.form'].browse([form_id])
        if not form:
            _logger.error('Form with id %s not found! Redirecting to startpage!' % str(form_id))
            return request.redirect("/")

        # FORM SUBMIT FOR EDIT BUTTON
        if kwargs.get('edit_form_data', False):
            # Set 'clear_session_data' to False before we redirect to the form again
            form_sdata = self.get_fso_form_session_data(form.id, check_clear_session_data=False)
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
