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
    #       website. Make sure the controller then checks these groups correctly!
    #       Default should be the public user of the website so all are allowed to view/use the form by default

    clear_session_data_after_submit = fields.Boolean(string="Clear Session Data after Submit",
                                                     default=True,
                                                     help="If set the form will be empty after a successful submit!")

    # Edit existing record if logged in TODO: add this to ghe form views
    edit_existing_record_if_logged_in = fields.Boolean(string="Edit existing record if logged in",
                                                       help="If set and a user is logged in (e.g. by token) he can edit"
                                                            " one existing record related to model linked to the form."
                                                            "If the current form model is not res.partner or res.user"
                                                            "you can mark a res.partner or res.user many2one field of"
                                                            "the form as the login field. The record in the form-model"
                                                            "where the marked field matches the logged in user (or the "
                                                            "users partner) can than be edited.\n"
                                                            "Clear Session Data after Submit will NOT WORK if this"
                                                            "is set and a user is logged in!")

    # TODO: !!!! E-Mail Stuff - only Fields are prepared right now !!!!
    email_only = fields.Boolean(string="E-Mail Only", help="Do !NOT! create a record but only send an E-Mail to the"
                                                           "information_email_receipients and the fields marked with"
                                                           "")
    confirmation_email_template = fields.Many2one(string='Confirmation Email Template',
                                                  comodel_name='email.template',
                                                  inverse_name="confirmation_email_template_fso_forms",
                                                  index=True)
    information_email_template = fields.Many2one(string='Information Email Template',
                                                 comodel_name='email.template',
                                                 inverse_name="information_email_template_fso_forms",
                                                 index=True)
    # TODO: Add an domain to only show partners with e-mails and no opt-out setting!
    information_email_receipients = fields.One2many(string='Information E-Mail Receipients',
                                                    comodel_name='res.partner',
                                                    inverse_name="information_email_receipient_fso_form")

    # Thank you page after submit
    thank_you_page_after_submit = fields.Boolean(string="Thank you page after submit!", default=True,
                                                 help="If set the form will be empty if called after a successful "
                                                      "submit without pressing the edit button on the thank you page!"
                                                      "Clear Session Data after submit has no effect then")
    # Technically this will pop the "clear_session_data" key from the form session data if set
    # so on the next hit the session data is still there and will not be removed!
    thank_you_page_edit_data_button = fields.Char(string="Edit Data Button", default=_('Edit'), translate=True,
                                                  help="If set a button will appear on the Thank You page to go "
                                                       "back to form to edit the data again!")
    thank_you_page_snippets = fields.Html(string="Thank you page", translate=True)

    @api.constrains('model_id', 'field_ids')
    def constrain_model_id_field_ids(self):
        for r in self:
            # Check all fields are fields of the current form_model
            if any(f.field_id.model_id != r.model_id for f in r.field_ids):
                raise ValidationError("Mismatch between some fields and current form model! "
                                      "Please remove fields for other models!")
            # Check that no field is marked as login field for res.partner or res.user forms
            login_fields = [f for f in r.field_ids if f.login]
            if r.model_id.model in ['res.partner', 'res.user'] and login_fields:
                raise ValidationError('Login fields are not allowed for partner ("res.partner") or user ("res.user") '
                                      'forms!')
            # Check that only one field is marked as a login field
            elif len([f for f in r.field_ids if f.login]) > 1:
                raise ValidationError("Only one login field is allowed per form!")
            # Check that fields are only used once!
            field_ids = [f.field_id.id for f in r.field_ids if f.field_id]
            if field_ids and len(field_ids) != len(set(field_ids)):
                duplicated_fields = set([f.field_id.name for f in r.field_ids
                                         if f.field_id and field_ids.count(f.field_id.id) > 1])
                raise ValidationError("A field is only allowed once in a form! Duplicated fields: %s "
                                      "" % str(duplicated_fields))
            # DISABLED: Check all regular required fields with no defaults are in the form!
            # ATTENTION: This is not possible to find out because some fields might get set in the CRUD mehtods!
            #            Therefore i disabled this check!
            # if r.model_id and r.field_ids:
            #     form_field_names = [f.field_id.name for f in r.field_ids]
            #     form_model = self.env[r.model_id.model].sudo()
            #     protected_fields = self.env['fson.form_field'].sudo()._protected_fields
            #     missing_required_fields = [fname for fname in form_model._fields if fname not in form_field_names
            #                                and fname not in protected_fields
            #                                and form_model._fields[fname].required
            #                                and not form_model._fields[fname].store
            #                                and not form_model._fields[fname].related
            #                                and not form_model._fields[fname].readonly
            #                                and not form_model._fields[fname].computed_fields
            #                                and not form_model._fields[fname].default]


class FSONFormField(models.Model):
    _name = "fson.form_field"
    _order = 'sequence'

    _allowed_field_types = ['boolean', 'char', 'selection', 'many2one', 'date', 'integer', 'float', 'binary']
    _protected_fields = set(MAGIC_COLUMNS + ['parent_left', 'parent_right',
                                             'sosync_fs_id', 'sosync_write_date', 'sosync_sync_date'])

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage', default=True)

    form_id = fields.Many2one(comodel_name="fson.form", string="Form", required=True,
                              index=True, ondelete='cascade')
    # ATTENTION: The domain is computed dynamically in the onchange method!
    field_id = fields.Many2one(string="Field", comodel_name='ir.model.fields',
                               index=True, ondelete='cascade')
    field_ttype = fields.Selection(string="Field Type", related='field_id.ttype', help='ttype',
                                   readonly=True, store=True)

    binary_name_field_id = fields.Many2one(string="File Name Field", comodel_name='ir.model.fields',
                                           domain="[('ttype','=','char'), "
                                                  " ('readonly','=',False), "
                                                  " ('name','not in',"+str(list(_protected_fields))+")]",
                                           index=True, ondelete='cascade')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True,
                              help="This is the placeholder text that will be shown inside of the input fields!"
                                   "For radio boxed styled boolean fields you can use this field to set the text for"
                                   "the yes and no radio boxes like this: "
                                   "{'yes': 'Sure i want this!', 'no': 'No thank you'}")
    yes_text = fields.Char(string="Yes Text", help="Only for radio-styled boolean fields!")
    no_text = fields.Char(string="No Text", help="Only for radio-styled boolean fields")
    mandatory = fields.Boolean(string='Mandatory', help="For boolean fields mandatory means you have to choose 'yes'"
                                                        "even if it is shown as a radio button!")
    nodata = fields.Boolean(string='No Data', help='Do not show/pre-fill data in the website form if logged in.')
    readonly = fields.Boolean(string='Read only if logged in',
                              help='Do not allow changing the data of the field if logged in and a record exits '
                                   'already! WARNING: This has NO effect if no record exists of no user is logged in!')
    login = fields.Boolean(string="Login Link", help="Only valid for many2one res.partner or res.user fields! "
                                                     "If set and the logged user relates to the partner or is the "
                                                     "user set in this field we try to load the corresponding record"
                                                     "and it's data to prefil the form and update the existing"
                                                     "record on form submit!")
    confirmation_email = fields.Boolean(string='Confirmation Email', help='Send a confirmation e-mail to this address')
    validation_rule = fields.Char(string='Frontend Validation', help="JQuery Frontend Validation Settings")
    css_classes = fields.Char(string='CSS classes', default='col-lg-6')
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    style = fields.Selection(selection=[('selection', 'Selection'),
                                        ('radio_selectnone', 'Radio + SelectNone'),
                                        ('radio', 'Radio')],
                             string='Field Style')
    information = fields.Html(string='Information', help='Information Text or Snippet Area if no field is selected!',
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
                # Check field ttype
                if r.field_id.ttype not in self._allowed_field_types:
                    raise ValidationError('Field type %s is not supported in form fields!' % r.field_id.ttype)
                # Check required fields
                if r.field_id.required and (not r.mandatory or not r.show):
                    raise ValueError('System-Required fields must have show and mandatory set to True in the form!')
                # Check binary_name_field_id
                if r.field_id.ttype != 'binary' and r.binary_name_field_id:
                    raise ValueError('"File Name" field must be empty for non binary fields!')
                # Check login field
                if r.login:
                    if r.field_ttype != 'many2one':
                        raise ValueError('The login field must be of type "many2one"!')
                    if r.field_id.model_name not in ['res.partner', 'res.user']:
                        raise ValueError('The login field must relate to the "res.partner" or "res.user" model!')
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

    @api.onchange('show', 'mandatory', 'field_id', 'binary_name_field_id', 'login')
    def oc_show(self):
        if not self.show:
            self.mandatory = False
        if self.field_id:
            if self.field_id.required:
                self.show = True
                self.mandatory = True
            if self.field_id.ttype != 'binary':
                self.binary_name_field_id = False
            if self.field_id.ttype not in ('selection', 'many2one', 'boolean'):
                self.style = False
            if self.form_id and self.form_id.model_id:
                if self.form_id.model_id.model in ['res.partner', 'res.user']:
                    self.login = False
        if self.binary_name_field_id:
            if not self.field_id or (self.field_id and self.field_id.ttype != 'binary'):
                self.binary_name_field_id = False

    @api.onchange('style', 'mandatory')
    def oc_style(self):
        if self.style == 'radio_selectnone':
            self.mandatory = False

    @api.onchange('field_id', 'form_id')
    def oc_field_id_dynamic_domain(self):
        field_id_domain = [('readonly', '=', False),
                           ('ttype', 'in', self._allowed_field_types),
                           ('name', 'not in', list(self._protected_fields))]
        if self.form_id and self.form_id.model_id:
            field_id_domain.append(('model_id', '=', self.form_id.model_id.id))

        return {'domain': {'field_id': field_id_domain}}

