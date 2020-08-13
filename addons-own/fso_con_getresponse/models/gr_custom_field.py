# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# ----------------
# Custom field mappings for GetResponse!
# ----------------
import re
import json

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from .backend import getresponse
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder


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

    _gr_field_prefix = 'frst_'
    _gr_type_mappings = {
        'boolean': ['checkbox'],
        'char': ['text', 'phone'],
        'text': ['textarea'],
        'selection': ['single_select', 'gender'],
        'many2one': ['single_select', 'country', 'gender'],
        'date': ['date'],
        'datetime': ['datetime'],
        'integer': ['number'],
        'float': ['number']
    }
    _gr_types_values_mandatory = ('checkbox', 'single_select', 'gender', 'country')
    _gr_models = ('res.partner', 'frst.personemail', 'frst.personemailgruppe')

    # ------
    # FIELDS
    # ------
    field_id = fields.Many2one(string="Field", comodel_name='ir.model.fields', inverse_name='gr_custom_field_ids',
                               required=True, index=True, ondelete='cascade',
                               domain=[('model_id.model', 'in', _gr_models)])
    field_ttype = fields.Selection(string="Field Type", related='field_id.ttype', help='ttype',
                                   readonly=True, store=True)
    field_model_name = fields.Char(string="Field Model", related='field_id.model_id.model', help='Model name',
                                   readonly=True, store=True)
    lang_id = fields.Many2one(comodel_name='res.lang', string='Language', required=True,
                              default=lambda self: self._default_lang_id()
                              )

    gr_name = fields.Char(string="GetResponse Field Name", compute="compute_gr_name", store=True, readonly=True)
    gr_type = fields.Selection(string="GetResponse Field Type",
                               required=True,
                               selection=[('text', 'text'),
                                          ('textarea', 'textarea'),
                                          ('checkbox', 'checkbox'),
                                          ('single_select', 'single_select'),
                                          ('number', 'number'),
                                          ('date', 'date'),
                                          ('datetime', 'datetime'),
                                          ('country', 'country'),
                                          ('phone', 'phone'),
                                          ('gender', 'gender')]
                               )
    gr_format = fields.Selection(string="GetResponse Field Format",
                                 selection=[('text', 'text'),
                                            ('textarea', 'textarea'),
                                            ('radio', 'radio'),
                                            ('checkbox', 'checkbox'),
                                            ('single_select', 'single_select')]
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

    # ----------
    # CONSTRAINS
    # ----------
    @api.constrains('field_id')
    def _constrain_field_id(self):
        for r in self:
            assert r.field_model_name in self._gr_models, (
                    "Only fields of the models '%s' are allowed!" % str(self._gr_models)
            )

    @api.constrains('field_id', 'gr_type')
    def _constrain_gr_type(self):
        for r in self:
            assert r.field_id.ttype in self._gr_type_mappings, (
                    "The odoo field type '%s' is not supported!" % r.field_id.ttype
            )
            assert r.gr_type in self._gr_type_mappings[r.field_id.ttype], (
                    "Wrong gr_type for the odoo field type %s! Please use one of %s "
                    "" % (r.field_id.ttype, self._gr_type_mappings[r.field_id.ttype])
            )

    @api.constrains('gr_values')
    def _constrain_gr_values(self):
        for r in self:
            # Check if gr_values is mandatory
            if r.gr_type in self._gr_types_values_mandatory:
                assert r.gr_values, "GetResponse Field Values is mandatory for gr_type '%s'" % r.gr_type
            else:
                assert not r.gr_values, "GetResponse Field Values must be empty for gr_type '%s'" % r.gr_type

    @api.constrains('lang_id')
    def constraint_lang_id(self):
        for r in self:
            assert r.lang_id.code == 'de_DE', "Only german 'de_DE' is supported!"

    # ---------------
    # COMPUTED FIELDS
    # ---------------
    @api.depends('field_id', 'lang_id')
    def compute_gr_name(self):
        for r in self:
            if r.field_id and r.lang_id and isinstance(r.id, int):
                assert r.lang_id.iso_code, (
                        "The selected language '%s' has no iso_code! Please add the iso_code!" % r.lang_id.name
                )
                gr_name = self._gr_field_prefix + 'id' + str(r.id) + '_' + r.lang_id.iso_code + '_' + r.field_id.name
                assert 12 <= len(gr_name) <= 128, "The gr_name '%s' must be between 10 and 128 characters!" % gr_name
                assert re.match(r"(?:[a-z0-9_]+)\Z", gr_name, flags=0), _(
                    "Only a-z, 0-9 and _ is allowed for the GetResponse field name: '{}'! ").format(gr_name)
                r.gr_name = gr_name
            else:
                r.gr_name = False

    # ------------
    # GUI ONCHANGE
    # ------------
    # Helper to create the json string with possible values for the custom field based on the selected odoo
    # field and the lang of the field
    @api.onchange('trigger_compute_gr_values')
    def compute_gr_values(self):
        for r in self:

            if not r.trigger_compute_gr_values:
                return

            # Make sure we get the values for the language set in for the field
            f_name = r.field_id.name
            f_model = r.field_model_name
            f_lang_code = r.lang_id.code
            assert f_lang_code, "Language of this field has no 'code'!"
            f_recordset_field_lang = r.env[f_model].with_context(lang=f_lang_code)

            values = []
            # SELECTION FIELD
            if r.field_ttype == 'selection':
                # Use fields_get() to get the selection values in the correct language
                # HINT: recordset._fields[f_name].selection will always use the en_us values (= values from the
                #       field-definition-code)
                # HINT: fields_get() will return a dict with all requested fields as the keys and in the correct lang!
                field_definitions = f_recordset_field_lang.fields_get([f_name])
                selection_list_correct_lang = field_definitions[f_name]['selection']
                selection_dict_correct_lang = dict(selection_list_correct_lang)
                values = selection_dict_correct_lang.values()
            # MANY2ONE FIELD
            elif r.field_ttype == 'many2one':
                f_comodel_name = r.field_id.relation
                records = f_recordset_field_lang.env[f_comodel_name].search([], limit=1000)
                values = records.mapped('name')
            # TODO: BOOLEAN FIELDS
            elif r.field_ttype == 'boolean':
                # TODO: I really dont understand why the getresponse checkbox type needs values?!?
                #       which values and how are they are mapped?!?! To be tested!
                values = ['true', 'false']

            # Check for duplicated entries
            unique_values = set()
            duplicates = []
            for value in values:
                if value not in unique_values:
                    unique_values.add(value)
                else:
                    duplicates.append(value)

            # Remove duplicates from unique_values completely
            # HINT: difference_update(): Remove all elements of another set from this set.
            unique_values.difference_update(set(duplicates))

            # Convert unique values json string
            unique_values_json = json.dumps(list(unique_values), encoding='utf-8', ensure_ascii=False).encode('utf8')

            # Append warning message if the limit was reached
            if len(values) > 999:
                warning_msg = 'WARNING: Limit of 1000 Records was reached! Values might be incomplete!\n\n'
                unique_values_json = warning_msg + unique_values_json

            # Append warning message if duplicates are found
            if duplicates:
                warning_msg = 'WARNING: Some values are not unique and therefore where removed! Removed duplicates:\n' \
                              '%s\n\n' % str(duplicates)
                unique_values_json = warning_msg + unique_values_json

            # Update gr_values and trigger_compute_gr_values
            r.gr_values = unique_values_json
            r.trigger_compute_gr_values = False

    # --------
    # METHODS
    # --------
    @api.model
    def _default_lang_id(self):
        german_lang = self.env['res.lang'].search([('code', '=', 'de_DE')], limit=1)
        return german_lang if len(german_lang) == 1 else False

    # -------------
    # CRUD AND COPY
    # -------------
    @api.multi
    def write(self, values):

        # Constrain changes to some fields after the field definition was created!
        for r in self:
            if 'field_id' in values and values['field_id'] != r.field_id.id:
                raise ValidationError("You can not change the linked field after the custom field was created!")
            if 'lang_id' in values and values['lang_id'] != r.lang_id.id:
                raise ValidationError("You can not change the language after the custom field was created!")
            if 'gr_name' in values and values['gr_name'] != r.gr_name:
                raise ValidationError("You can not change the gr_name after the custom field was created!")
            if 'gr_type' in values and values['gr_type'] != r.gr_type:
                raise ValidationError("You can not change the gr_type after the custom field was created!")
            if 'gr_format' in values and values['gr_format'] != r.gr_format:
                raise ValidationError("You can not change the gr_format after the custom field was created!")

        return super(GrCustomField, self).write(values)


class GetResponseIrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    gr_custom_field_ids = fields.One2many(string="GetResponse Custom Fields ",
                                          comodel_name='gr.custom_field', inverse_name='field_id')
