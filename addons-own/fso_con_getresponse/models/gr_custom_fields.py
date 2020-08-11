# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# ----------------
# Custom field mappings for GetResponse!
# ----------------
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from .backend import getresponse
from .unit_adapter import GetResponseCRUDAdapter
from.unit_binder import GetResponseBinder

import re


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GrCustomFields(models.Model):
    _name = 'gr.custom_fields'
    _description = 'GetResponse Custom Fields'

    _gr_field_prefix = 'frst_'
    _gr_types = {'boolean': ['checkbox'],
                 'char': ['text', 'phone'],
                 'text': ['textarea'],
                 'selection': ['single_select', 'gender'],
                 'many2one': ['single_select', 'country', 'gender'],
                 'date': ['date'],
                 'datetime': ['datetime'],
                 'integer': ['number'],
                 'float': ['number']}
    _gr_models = ('res.partner', 'frst.personemail', 'frst.personemailgruppe')

    # ------
    # FIELDS
    # ------
    field_id = fields.Many2one(string="Odoo Field", comodel_name='ir.model.fields',
                               required=True, index=True, ondelete='cascade')
    gr_name = fields.Char(string="GetResponse Field Name", compute="compute_gr_name", store=True, readonly=True)
    gr_type = fields.Selection(string="GetResponse Field Type", required=True,
                               selection=[('text', 'text'),
                                          ('textarea', 'textarea'),
                                          ('checkbox', 'checkbox'),
                                          ('number', 'number'),
                                          ('date', 'date'),
                                          ('datetime', 'datetime'),
                                          ('country', 'country'),
                                          ('phone', 'phone'),
                                          ('gender', 'gender'),
                                          ])
    gr_format = fields.Selection(string="GetResponse Field Format",
                                 selection=[('text', 'text'),
                                            ('textarea', 'textarea'),
                                            ('radio', 'radio'),
                                            ('checkbox', 'checkbox'),
                                            ('single_select', 'single_select')
                                            ])
    gr_hidden = fields.Boolean(string="GetResponse Hidden")
    gr_values = fields.Char(string="GetResponse Field Values",
                            help="JSON string with possible values for the GetResponse field")

    @api.constrains('gr_type')
    def _constrain_gr_type(self):
        for r in self:
            assert r.field_id.ttype in self._gr_types, "This odoo field type is not supported: %s" % r.field_id.ttype
            assert r.gr_type in self._gr_types[r.field_id.ttype], "Wrong gr_type for the odoo field type %s! " \
                                                                  "Please use one of %s " \
                                                                  "" % (r.field_id.ttype,
                                                                        self._gr_types[r.field_id.ttype])

    @api.depends('field_id')
    def compute_gr_name(self):
        for r in self:
            gr_name = self._gr_field_prefix + r.field_id.name
            assert 128 <= len(gr_name) >= 1, "The gr_name must be between 1 and 128 characters long!"
            assert re.match(r"(?:[a-z0-9_]+)\Z", gr_name, flags=0), _(
                "Only a-z, 0-9 and _ is allowed for the GetResponse field name '{}'! ").format(gr_name)
            r.gr_name = self._gr_field_prefix + r.field_id.name

    @api.depends('field_id')
    def compute_gr_values(self):
        for r in self:
            # Get values for a selection field
            r.gr_name = self._gr_field_prefix + r.field_id.name
            # Get Values for a many2one field

    @api.multi
    def write(self, values):
        for r in self:
            field_id = values.get('field_id', None)
            if field_id:
                assert field_id == r.field_id.id, "You can not change the linked field after the custom field was " \
                                                  "created!"
