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


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GrCustomFields(models.Model):
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
    _sql_constraints = [
        ('field_id_uniq', 'unique(field_id)',
         'A GetResponse Custom Field Definition already exists for the odoo field with this id.'),
    ]

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

    # --------
    # COMPUTED
    # --------
    @api.depends('field_id', 'lang_id')
    def compute_gr_name(self):
        for r in self:
            if r.field_id and r.lang_id:
                assert r.lang_id.iso_code, (
                        "The selected language '%s' has no iso_code! Please add the iso_code!" % r.lang_id.name
                )
                gr_name = self._gr_field_prefix + r.lang_id.iso_code + '_' + r.field_id.name
                assert 10 <= len(gr_name) <= 128, "The gr_name '%s' must be between 10 and 128 characters!" % gr_name
                assert re.match(r"(?:[a-z0-9_]+)\Z", gr_name, flags=0), _(
                    "Only a-z, 0-9 and _ is allowed for the GetResponse field name: '{}'! ").format(gr_name)
                r.gr_name = gr_name
            else:
                r.gr_name = False

    # --------
    # METHODS
    # --------
    @api.model
    def _default_lang_id(self):
        german_lang = self.env['res.lang'].search([('code', '=', 'de_DE')], limit=1)
        return german_lang if len(german_lang) == 1 else False

    # TODO: Helper to create the json string with possible values for the custom field based on the selected odoo
    #       field and the lang of the field
    @api.onchange('trigger_compute_gr_values')
    def compute_gr_values(self):
        for r in self:

            if not r.trigger_compute_gr_values:
                return

            context_lang = self.env.context.get('lang', None)
            field_lang_code = r.lang_id.code
            assert field_lang_code, "Language of this field has no 'code'!"
            res = []
            # selection field
            if r.field_ttype == 'selection':
                f_name = r.field_id.name
                f_model = r.field_model_name
                f_recordset_correct_lang = r.env[f_model].with_context(lang=field_lang_code)
                # Use fields_get() to get the selection values in the correct language
                # HINT: recordset._fields[f_name].selection will always use the en_us values (= values from the
                #       field-definition-code)
                # HINT: fields_get() will return a dict with all requested fields as the keys
                selection_list_correct_lang = f_recordset_correct_lang.fields_get([f_name])[f_name]['selection']
                selection_dict_correct_lang = dict(selection_list_correct_lang)
                res = selection_dict_correct_lang.values()
            # many2one field
            elif r.field_ttype == 'many2one':
                records = self.env[r.field_model_name].search([])
                res = records.mapped('name')
                if len(records) != res:
                    res = ['WARNING: Record names are not unique!\n'].append(res)
            # Boolean field
            elif r.field_ttype == 'boolean':
                # TODO: I really dont understand why the checkbox needs values - which values?!?! to be tested!
                res = ['true', 'false']

            # Convert to json string
            res_json = json.dumps(res, encoding='utf8', ensure_ascii=False)

            # Update gr_values
            r.gr_values = res_json
            r.trigger_compute_gr_values = False
            #return {'value': {'gr_values': res_json, 'trigger_compute_gr_values': False}}

    # -------------
    # CRUD AND COPY
    # -------------
    @api.multi
    def write(self, values):
        for r in self:
            if 'field_id' in values and values['field_id'] != r.field_id.id:
                raise ValidationError("You can not change the linked field after the custom field was created!")
            if 'lang_id' in values and values['lang_id'] != r.lang_id.id:
                raise ValidationError("You can not change the language after the custom field was created!")
            if 'gr_name' in values and values['gr_name'] != r.gr_name:
                raise ValidationError("You can not change the gr_name after the custom field was created!")

        return super(GrCustomFields, self).write(values)


class GetResponseIrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    gr_custom_field_ids = fields.One2many(string="GetResponse Custom Fields ",
                                          comodel_name='gr.custom_field', inverse_name='field_id')
