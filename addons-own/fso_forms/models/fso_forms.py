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
                                 help="Subission URL for form data! Do not set unless you really need to!"
                                      "If set no record will be")
    redirect_url = fields.Char(string="Redirect URL", default=False,
                               help="Redirect URL after form feedback! Do not set unless you really need to!"
                                    "If set the Thank You Page will not be called!")
    submit_button_text = fields.Char(string="Submit Button Text", default=_('Submit'), required=True, translate=True)

    frontend_validation = fields.Boolean(string="Frontend Validation", default=True,
                                         help="Enable JavaScript-Frontend-Form-Validation by jquery-validate!")

    snippet_area_top = fields.Html(string="Top Snippet Area", translate=True)
    snippet_area_bottom = fields.Html(string="Bottom Snippet Area", translate=True)

    # TODO: Add this to the <head> section of website.layout somehow :)
    custom_css = fields.Text(string="Custom CSS", help="TODO! This is not working yet!!!")

    # TODO: Add a user_group_ids and user_ids field to set what Users and or groups are allowed to view a form
    #       Make sure the controller then checks these fields
    #       Default should be the public user of the website so all are allowed to view/use the form by default

    clear_session_data_after_submit = fields.Boolean(string="Clear Session Data after Submit",
                                                     help="If set the form will be empty after a successful submit!")

    # Thank you page after submit
    thank_you_page_after_submit = fields.Boolean(string="Thank you page after submit!", default=True,
                                                 help="If set the form will be empty if called after a successful "
                                                      "submit without pressing the edit button on the thank you page!"
                                                      "Clear Session Data after submitt has no effect then")
    # Technically this will pop the "clear_session_data" key from the form session data if set
    # so on the next hit the session data is still there and will not be removed!
    thank_you_page_edit_data_button = fields.Char(string="Edit Data Button", default=_('Edit'), translate=True,
                                                  help="If set a button will appear on the Thank You page to go "
                                                       "back to form to edit the data again!")
    thank_you_page_snippets = fields.Html(string="Thank you page", translate=True)

    @api.constrains('model_id')
    def constrain_model_id(self):
        for r in self:
            if any(f.field_id.model_id != r.model_id for f in r.field_ids):
                raise ValidationError("Mismatch between some fields and current form model! "
                                      "Please remove fields for other models!")
            # TODO: Make sure all ORM-Required fields of the model with no default value are in the form!
            # TODO: Make sure a field (field_id) is only used once!


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

    binary_name_field_id = fields.Many2one(string="File Name Field", comodel_name='ir.model.fields',
                                           domain="[('ttype','=','char'), "
                                                  " ('readonly','=',False), "
                                                  " ('name','not in',"+str(list(_protected_fields))+")]",
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

    # TODO: Add file type or mime type restrictions for binary fields
    #       HINT: check html  parameter 'accept' and 'type'

    @api.constrains('field_id', 'binary_name_field_id')
    def constrain_field_id(self):
        for r in self:
            if r.field_id:
                # Check readonly
                if r.field_id.readonly:
                    raise ValidationError('You can not add readonly fields!')
                # Check protected fields
                if r.field_id.name in self._protected_fields:
                    raise ValidationError('Protected and system fields are not allowed!')
                # Check required fields
                if r.field_id.required and (not r.mandatory or not r.show):
                    raise ValueError('System-Required fields must have show and mandatory set to True in the form!')
                # Check binary_name_field_id
                if r.field_id.ttype != 'binary' and r.binary_name_field_id:
                    raise ValueError('"File Name" field must be empty for non binary fields!')
            if r.binary_name_field_id:
                # Check field_id
                if not r.field_id or (r.field_id and r.field_id.ttype != 'binary'):
                    raise ValueError('"File Name" field must be empty for non binary fields!')
                # Check readonly
                if r.binary_name_field_id.readonly:
                    raise ValidationError('"File Name" field is readonly!')
                # Check protected fields
                if r.binary_name_field_id.name in self._protected_fields:
                    raise ValidationError('"File Name" field can not be a protected or system field!')
                # Check required fields
                if r.binary_name_field_id.required and (not r.mandatory or not r.show):
                    raise ValueError('Required fields must have show and mandatory set to True in the form!')

    @api.onchange('show', 'mandatory', 'field_id', 'binary_name_field_id')
    def oc_show(self):
        if not self.show:
            self.mandatory = False
        if self.field_id:
            if self.field_id.required:
                self.show = True
                self.mandatory = True
            if self.field_id.ttype != 'binary':
                self.binary_name_field_id = False
        if self.binary_name_field_id:
            if not self.field_id or (self.field_id and self.field_id.ttype != 'binary'):
                self.binary_name_field_id = False

    @api.onchange('style', 'mandatory')
    def oc_style(self):
        if self.style == 'radio_selectnone':
            self.mandatory = False
