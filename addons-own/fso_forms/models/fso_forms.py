# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.tools import SUPERUSER_ID
from openerp.models import MAGIC_COLUMNS

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _name = "fson.form"

    _order = 'sequence'

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    name = fields.Char(string="Form Name", required=True)

    model_id = fields.Many2one(string="Model", comodel_name="ir.model", required=True)
    field_ids = fields.One2many(string="Fields", comodel_name="fson.form_field", inverse_name="form_id")

    submission_url = fields.Char(string="Submission URL", default=False,
                                 help="Subission URL for form data! Do not set unless you really need to!")
    redirect_url = fields.Char(string="Redirect URL", default=False,
                               help="Redirect URL after form feedback! Do not set unless you really need to!")
    submit_button_text = fields.Char(string="Submit Button Text", default=_('Submit'), required=True)

    frontend_validation = fields.Boolean(string="Frontend Validation", default=True,
                                         help="Enable JavaScript-Frontend-Form-Validation by jquery-validate!")

    snippet_area_top = fields.Html(string="Top Snippet Area")
    snippet_area_bottom = fields.Html(string="Bottom Snippet Area")

    @api.constrains('model_id')
    def constrain_model_id(self):
        for r in self:
            if any(f.field_id.model_id != r.model_id for f in r.field_ids):
                raise ValidationError("Mismatch between some fields and current form model! "
                                      "Please remove fields for other models!")


class FSONFormField(models.Model):
    _name = "fson.form_field"
    _order = 'sequence'

    _protected_fields = set(MAGIC_COLUMNS + ['parent_left', 'parent_right',
                                             'sosync_fs_id', 'sosync_write_date', 'sosync_sync_date'])

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage', default=True)

    form_id = fields.Many2one(comodel_name="fson.form", string="Form", required=True,
                              index=True, ondelete='cascade')

    field_id = fields.Many2one(string="Field", comodel_name='ir.model.fields',
                               index=True, ondelete='cascade')

    mandatory = fields.Boolean(string='Mandatory')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True)
    validation_rule = fields.Char(string='Validation Rule')
    css_classes = fields.Char(string='CSS classes', default='col-lg-6')
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    nodata = fields.Boolean(string='NoData', help='Do not show record data in the website form if logged in.')
    style = fields.Selection(selection=[('selection', 'Selection'),
                                        ('radio_selectnone', 'Radio + SelectNone'),
                                        ('radio', 'Radio')],
                             string='Field Style')
    information = fields.Html(string='Information', help='Information Text. Snippet Area if no Field is not set!',
                              translate=True)

    # TODO: set or select file name field for binary fields somehow
    # TODO: file type restrictions for binary fields check the
    #       HINT: check html spec type= input and parameter accept and type (for mime type)

    # TODO: Add a field for custom css to quickly override form styles :) (new Tab "Dangerzone" :) in backend)

    @api.constrains('field_id')
    def constrain_field_id(self):
        for r in self:
            if r.field_id:
                # Check readonly
                if r.field_id.readonly:
                    raise ValidationError('You can not add readonly fields to a fso_form!')
                # Check protected fields
                if r.field_id.name in self._protected_fields:
                    raise ValidationError('Protected and system fields are not allowed!')
                # Check required fields
                if r.field_id.required and (not r.mandatory or not r.show):
                    raise ValueError('Required fields must have show and mandatory set to True in the form!')

    @api.onchange('show', 'mandatory', 'field_id')
    def oc_show(self):
        if not self.show:
            self.mandatory = False
        if self.field_id:
            if self.field_id.required:
                self.show = True
                self.mandatory = True

    @api.onchange('style', 'mandatory')
    def oc_style(self):
        if self.style == 'radio_selectnone':
            self.mandatory = False

    # TODO: Maybe not needed!
    @api.onchange('form_id')
    def oc_form_id(self):
        if self.form_id:
            return {'domain': {
                'form_id': [('model_id', '=', self.form_id.model_id)]
            }}
