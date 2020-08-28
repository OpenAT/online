# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# ----------------
# Custom field mappings for GetResponse!
# HINT: Only values that are in the custom field definition can be used for a custom field - therefore all values
#       should always be in the field definition. Also there is no empty value - therefore we use _gr_false_value
# ----------------
import logging
import re
import json
import datetime

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GrCustomField(models.Model):
    """ Custom Field Definitions for the GetResponse import and export of e-mail subscriptions
    (contact <> PersonEmalGruppe + PersonEmail + Person)

    An odoo field may have multiple definitons for different languages and values. Therefore the official in charge for
    the forms and settings in GetResponse must make sure that only one field per campaign/form/contact is used or there
    will be errors or unexpected values when importing the contact!
    """
    _name = 'gr.custom_field'
    _description = 'GetResponse Custom Fields'

    _gr_field_prefix = 'frst__'

    _gr_false_key = 'false'
    _gr_true_key = 'true'
    _gr_false_value = {_gr_false_key: _('keine Angabe')}

    # ATTENTION: 'one2many' and 'many2many' are not supported! (check constrains below)
    _gr_type_mappings = {
        'boolean': ['checkbox'],
        'char': ['text', 'phone', 'url', 'ip'],
        'text': ['textarea'],
        'selection': ['single_select', 'gender'],
        'many2one': ['single_select', 'country', 'gender'],
        'one2many': ['multi_select', 'currency', 'country'],
        'many2many': ['multi_select', 'currency', 'country'],
        'date': ['date'],
        'datetime': ['datetime'],
        'integer': ['number'],
        'float': ['number']
    }
    _gr_types_values_mandatory = ('checkbox', 'single_select', 'gender', 'country', 'multi_select', 'currency')
    _gr_models = ('res.partner', 'frst.personemail', 'frst.personemailgruppe')

    # Buffer to prevent redundant searches in the db
    _gr_watched_fields = None

    # ------
    # FIELDS
    # ------
    # HINT: A default name is either generated in odoo or comes from a getresponse import!
    #       Therefore the user can not choose the getresponse name for this field!
    name = fields.Char(string='Name', required=True)

    # HINT: This default also means that we assume that every imported field from GetResponse is 'german'!
    lang_id = fields.Many2one(comodel_name='res.lang', string='Language', required=True,
                              default=lambda self: self._default_lang_id()
                              )

    # Odoo field type and field values language
    field_id = fields.Many2one(string="Field", comodel_name='ir.model.fields', inverse_name='gr_custom_field_ids',
                               index=True, ondelete='cascade',
                               domain=[('model_id.model', 'in', _gr_models)])
    field_ttype = fields.Selection(string="Field Type", related='field_id.ttype', help='ttype',
                                   readonly=True, store=True)
    field_model_name = fields.Char(string="Field Model", related='field_id.model_id.model', help='Model name',
                                   readonly=True, store=True)

    # GetResponse custom field data
    gr_type = fields.Selection(string="GetResponse Field Type",
                               required=True,
                               selection=[('text', 'text'),
                                          ('textarea', 'textarea'),
                                          ('radio', 'radio'),
                                          ('checkbox', 'checkbox'),
                                          ('single_select', 'single_select'),
                                          ('multi_select', 'multi_select'),
                                          ('number', 'number'),
                                          ('date', 'date'),
                                          ('datetime', 'datetime'),
                                          ('country', 'country'),
                                          ('phone', 'phone'),
                                          ('gender', 'gender'),
                                          ('ip', 'ip'),
                                          ('url', 'url')]
                               )
    gr_format = fields.Selection(string="GetResponse Field Format",
                                 selection=[('text', 'text'),
                                            ('textarea', 'textarea'),
                                            ('radio', 'radio'),
                                            ('checkbox', 'checkbox'),
                                            ('single_select', 'single_select'),
                                            ('multi_select', 'multi_select')]
                                 )
    gr_hidden = fields.Selection(string="GetResponse Hidden",
                                 required=True,
                                 selection=[('true', 'Hidden for Contacts'),
                                            ('false', 'Visible for Contacts')
                                            ],
                                 default='false',
                                 help="Whether the custom field is visible to contacts in GetResponse")
    trigger_compute_gr_values = fields.Boolean(string="Trigger compute GetResponse Field Values",
                                               help="This is just a helper field to trigger the onchange method."
                                                    "It is not important if set to True of False!")
    gr_values = fields.Text(string="GetResponse Field Values",
                            help="JSON string with possible values for the GetResponse custom field")

    # Store some extra infos for the generated values
    gr_values_mappings = fields.Text(string="Field Value Mappings",
                                     help="JSON string with 'values to ids' mappings for the GetResponse custom field."
                                          " This is just a helper to be able to detect if 'value to id' mapping has"
                                          " changed. Please do not change this field manually!")

    # ----------
    # CONSTRAINS
    # ----------
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'A custom field with this name exists already.'),
    ]

    @api.constrains('name')
    def _constrain_name(self):
        for r in self:
            assert 2 <= len(r.name) <= 128, "The name '%s' must be between 10 and 128 characters!" % r.name
            assert re.match(r"(?:[a-z0-9_]+)\Z", r.name, flags=0), _(
                "Only a-z, 0-9 and _ is allowed for the a GetResponse Custom Field name: '{}'! ").format(r.name)

    @api.constrains('lang_id')
    def _constraint_lang_id(self):
        for r in self:
            assert r.lang_id.code == 'de_DE', "Only german 'de_DE' is supported!"

    @api.constrains('field_id', 'name')
    def _constrain_field_id(self):
        for r in self:
            if r.field_id:
                assert r.field_model_name in self._gr_models, _(
                        "Only odoo fields of the models '%s' are allowed!" % str(self._gr_models))
                assert r.name.startswith(self._gr_field_prefix), _(
                    "Only custom field definitions created in FS-Online are allowed to be mapped to odoo fields!")

    @api.constrains('field_id', 'gr_type')
    def _constrain_gr_type(self):
        for r in self:
            if r.field_id:
                assert r.field_ttype not in ('one2many', 'many2many'), (
                        "The odoo field type '%s' is not supported!" % r.field_ttype
                )
                assert r.gr_type in self._gr_type_mappings[r.field_ttype], (
                        "Wrong gr_type for the odoo field type '%s'! Please use one of '%s'."
                        "" % (r.field_ttype, self._gr_type_mappings[r.field_ttype])
                )

    @api.constrains('gr_values')
    def _constrain_gr_values(self):
        for r in self:
            # Check if gr_values is mandatory
            if r.gr_type in self._gr_types_values_mandatory:
                assert r.gr_values, "GetResponse Field Values is mandatory for gr_type '%s'" % r.gr_type
            else:
                assert not r.gr_values, "GetResponse Field Values must be empty for gr_type '%s'" % r.gr_type
            # Check if the data is valid json and a list
            if r.gr_values:
                try:
                    data = json.loads(r.gr_values, encoding='utf-8')
                except Exception as e:
                    raise ValueError("gr_values must be a valid json string!\n%s\n'%s'" % (r.gr_values, e.message))
                assert isinstance(data, list), "gr_values must be a list of strings!"

    # ------------
    # GUI ONCHANGE
    # ------------
    @api.onchange('field_id', 'lang_id')
    def _onchange_name(self):
        for r in self:
            if r.field_id and r.lang_id:
                if not r.name or r.name.startswith(self._gr_field_prefix):
                    r.name = r._default_name()

    @api.onchange('gr_values')
    def _onchange_gr_values(self):
        for r in self:
            # Clear gr_values_mappings in case gr_values gets cleared
            if not r.gr_values and r.gr_values_mappings:
                r.gr_values_mappings = False

    # Helper to create the json string with possible values for the custom field based on the selected odoo
    # field and the lang of the field
    # TODO: Split the functions in smaller methods and use them in record_to_gr_value() to return the correct value!
    @api.onchange('trigger_compute_gr_values')
    def _onchange_gr_values(self):
        for r in self:
            if not r.trigger_compute_gr_values:
                return

            # Make sure we get the values for the language set in for the field
            f_name = r.field_id.name
            f_model = r.field_model_name
            f_lang_code = r.lang_id.code
            assert f_lang_code, "Language of this field has no 'code'!"
            f_recordset_field_lang = r.env[f_model].with_context(lang=f_lang_code)

            value_mappings = {}

            # SELECTION FIELD
            if r.field_ttype == 'selection':
                # Use fields_get() to get the selection values in the correct language
                # HINT: recordset._fields[f_name].selection will always use the en_us values (= values from the
                #       field-definition-code)
                # HINT: fields_get() will return a dict with all requested fields as the keys and in the correct lang!
                field_definitions = f_recordset_field_lang.fields_get([f_name])
                selection_list_correct_lang = field_definitions[f_name]['selection']
                value_mappings = dict(selection_list_correct_lang)

                # Add a way to 'clear' non mandatory fields
                if not r.field_id.required:
                    value_mappings.update(self._gr_false_value)

            # MANY2ONE FIELD
            elif r.field_ttype == 'many2one':
                f_comodel_name = r.field_id.relation
                records = f_recordset_field_lang.env[f_comodel_name].search([], limit=1000)
                # TODO: allow other fields of the related model than just name
                value_mappings = {str(r.id): r.name for r in records}

                # Add a way to 'clear' non mandatory fields
                if not r.field_id.required:
                    value_mappings.update(self._gr_false_value)

            # BOOLEAN FIELD
            elif r.field_ttype == 'boolean':
                # TODO: I really dont understand why the getresponse checkbox type needs values?!?
                #       which values and how are they are mapped?!?! To be discovered ;)
                value_mappings = {self._gr_true_key: self._gr_true_key,
                                  self._gr_false_key: self._gr_false_key}

            # Check for duplicated values in the dict
            seen_values = {}
            unique_value_mappings = {}
            duplicated_value_mappings = {}
            for key, value in value_mappings.iteritems():
                # The value is not a key in the seen_values dict (no duplicated value)
                if value not in seen_values:
                    seen_values[value] = key
                    unique_value_mappings[key] = value
                # The value is already a key in the seen_values dict (is a duplicated value)
                else:
                    # Remove the duplicated value entry from the unique_value_mappings dict and store the removed
                    # key / value pair in 'duplicated_value_mappings'
                    if seen_values[value] in unique_value_mappings:
                        duplicated_value_mappings[seen_values[value]] = unique_value_mappings.pop(seen_values[value])
                    # Add the entry to the duplicated_value_mappings dict
                    duplicated_value_mappings[key] = value

            # Convert unique values json string
            unique_values = unique_value_mappings.values()
            unique_values_json = json.dumps(unique_values, encoding='utf-8', ensure_ascii=False)

            # Append warning message if the limit was reached
            if len(unique_values) > 999:
                warning_msg = 'WARNING: Limit of 1000 Records was reached! Values might be incomplete!\n\n'
                unique_values_json = warning_msg + unique_values_json

            # Append warning message if duplicates are found
            if duplicated_value_mappings:
                warning_msg = 'WARNING: Some values are not unique and therefore where removed! Removed duplicates:\n' \
                              '%s\n\n' % str(duplicated_value_mappings)
                unique_values_json = warning_msg + unique_values_json

            # Update gr_values and trigger_compute_gr_values
            r.gr_values = unique_values_json
            r.gr_values_mappings = json.dumps(seen_values, encoding='utf-8', ensure_ascii=False)
            r.trigger_compute_gr_values = False

    # --------
    # METHODS
    # --------
    @api.model
    def _default_lang_id(self):
        german_lang = self.env['res.lang'].search([('code', '=', 'de_DE')], limit=1)
        return german_lang if len(german_lang) == 1 else False

    @api.multi
    def _default_name(self):
        self.ensure_one()
        r = self

        # Add the generic field prefix for custom fields created in odoo
        name = self._gr_field_prefix

        # Add the language code (lowercase)
        name += r.lang_id.code.lower() + '__'
        # Add the odoo field id
        name += 'fid' + str(r.field_id.id) + '__'
        # Add the odoo field name (lowercase)
        name += r.field_id.name.lower() + '__'
        # Add a unique number
        name += datetime.datetime.now().strftime('%y%m%d%M%S')

        return name

    @api.multi
    def update_checks(self, values):
        if self.env.context.get('skipp_write_checks', False):
            return

        for r in self:
            if 'name' in values and values['name'] != r.name:
                raise ValidationError("You can not change the field name '%s' after the custom field was"
                                      " created!" % r.name)
            if 'field_id' in values and values['field_id'] != r.field_id.id:
                raise ValidationError("You can not change the odoo field after the custom field was created!")
            if 'lang_id' in values and values['lang_id'] != r.lang_id.id:
                raise ValidationError("You can not change the language after the custom field was created!")

            if 'gr_type' in values and values['gr_type'] != r.gr_type:
                raise ValidationError("You can not change the gr_type after the custom field was created!")
            # We do allow to change gr_format if not yet set
            if 'gr_format' in values and r.gr_format and values['gr_format'] != r.gr_format:
                raise ValidationError("You can not change the gr_format after the custom field was created!")

    # Get a Custom field and a record and return the correct value like in the gr_values field!
    # TODO: Split the functions in _onchange_gr_values() in smaller methods and use them here!
    @api.multi
    def record_to_gr_value(self, record):
        self.ensure_one()
        record.ensure_one()
        custom_field = self
        assert custom_field.field_id, "The custom field %s is not mapped to an odoo field!" % custom_field.id
        assert custom_field.field_model_name == record._name, (
            "The model of the given record (%s, %s) is not matching the custom field odoo field model (%s, %s)!"
            "" % (record._name, record.id, custom_field.field_model_name, custom_field.id)
        )

        # Make sure we get the values for the language set in for the field
        cf_lang_code = custom_field.lang_id.code
        assert cf_lang_code, "Language of custom field %s has no 'code'!" % custom_field.id
        if record.env.context.get('lang') != cf_lang_code:
            _logger.error('Language of the record (%s, %s) is not matching the language of the custom field (%s, %s)!'
                          '' % (record._name, record.id, custom_field.name, custom_field.id))
            record = record.with_context(lang=cf_lang_code)


        cf_odoo_field_name = custom_field.field_id.name

        # Get the value from the record for the mapped odoo field in the GetResponse Custom Field Definition
        record_cf_field_value = record[cf_odoo_field_name]

        _gr_not_selected_value = self._gr_false_value.get(self._gr_false_key)

        # SELECTION FIELD
        if custom_field.field_ttype == 'selection':
            # TODO: This may not handle selection field with a possible value of ('', '') correctly
            if not record_cf_field_value:
                gr_value = _gr_not_selected_value
            else:
                field_definitions = record.fields_get([cf_odoo_field_name])
                selection_vals = field_definitions[cf_odoo_field_name]['selection']
                selection_vals_dict = dict(selection_vals)
                gr_value = selection_vals_dict[record_cf_field_value]

        # MANY2ONE FIELD
        elif custom_field.field_ttype == 'many2one':
            # TODO: allow other fields of the related model than just 'name'
            related_record = record[cf_odoo_field_name]
            gr_value = related_record.name if related_record else False
            if not gr_value:
                gr_value = _gr_not_selected_value

        # BOOLEAN FIELD
        elif custom_field.field_ttype == 'boolean':
            gr_value = 'true' if record[cf_odoo_field_name] else 'false'

        # ALL OTHER FIELDS
        else:
            gr_value = record[cf_odoo_field_name]

        return gr_value

    @api.multi
    def get_odoo_value(self, raw_value):
        """ Get a GetResponse Value and convert it to the correct odoo value """
        # Works only with a singe custom field
        self.ensure_one()
        custom_field = self

        if custom_field.field_ttype == 'boolean':
            assert raw_value in ('true', 'false'), "'true' or 'false' expected for a boolean field! %s" % raw_value
            odoo_value = True if raw_value == 'true' else False

        elif custom_field.field_ttype in ('selection', 'many2one'):
            mappings = json.loads(custom_field.gr_values_mappings, encoding='utf-8')
            # TODO: We may also search for the odoo value in the future... right now it must be in the
            #       gr_values_mappings keys!
            assert raw_value in mappings, "Custom field value '%s' not found in gr_values_mappings keys!" % raw_value
            odoo_value = mappings['raw_value']

        else:
            odoo_value = raw_value

        return odoo_value

    @api.model
    def watched_fields(self):

        # HINT: The buffer will be reset in the crud methods
        if self._gr_watched_fields is None:
            custom_field_names = {}
            mapped_custom_fields = self.sudo().search([('field_id', '!=', False)])
            for f in mapped_custom_fields:
                if f.field_model_name not in custom_field_names:
                    custom_field_names[f.field_model_name] = [f.field_id.name]
                else:
                    custom_field_names[f.field_model_name].append(f.field_id.name)
            self._gr_watched_fields = custom_field_names

        return self._gr_watched_fields

    # -------------
    # CRUD AND COPY
    # -------------
    @api.model
    def create(self, values):

        # Unset _gr_watched_fields buffer
        self._gr_watched_fields = None

        return super(GrCustomField, self).create(values)

    @api.multi
    def write(self, values):

        # Unset _gr_watched_fields buffer
        if values:
            self._gr_watched_fields = None

        # Disallow changes to some fields after the custom field was created!
        self.update_checks(values)

        return super(GrCustomField, self).write(values)

    @api.multi
    def unlink(self):

        # Unset _gr_watched_fields buffer
        self._gr_watched_fields = None

        return super(GrCustomField, self).unlink()


class GetResponseIrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    gr_custom_field_ids = fields.One2many(string="GetResponse Custom Fields ",
                                          comodel_name='gr.custom_field', inverse_name='field_id')
