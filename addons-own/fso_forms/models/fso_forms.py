# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.tools import SUPERUSER_ID
from openerp.models import MAGIC_COLUMNS

from lxml import etree

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _name = "fson.form"

    _order = 'sequence'

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    name = fields.Char(string="Form Name", required=True)

    model_id = fields.Many2one(string="Model", comodel_name="ir.model", required=True)
    field_ids = fields.One2many(string="Fields", comodel_name="fson.form_field", inverse_name="form_id")

    create_as_user = fields.Many2one(string="Create as user", comodel_name="res.users",
                                     help="ALWAYS create new records with this user!")

    submission_url = fields.Char(string="Submission URL", default=False,
                                 help="Subission URL for form data! Do not set unless you really need to!"
                                      "If set no record will be")

    redirect_url = fields.Char(string="Redirect URL", default=False,
                               help="Redirect URL after form feedback! Do not set unless you really need to!"
                                    "If set the Thank You Page will not be called!")
    redirect_url_target = fields.Selection(selection=[('_parent', '_parent'),
                                                      ('_blank', '_blank')],
                                           string="Redirect URL target")
    redirect_url_if_logged_in = fields.Char(string="Redirect URL if logged in", default=False,
                                            help="Redirect URL after form feedback if logged in! "
                                                 "Do not set unless you really need to!"
                                                 "If set the Thank You Page will not be called!")
    redirect_url_if_logged_in_target = fields.Selection(selection=[('_parent', '_parent'),
                                                                   ('_blank', '_blank')],
                                                        string="Redirect URL if logged in target")

    submit_button_text = fields.Char(string="Submit Button Text", default=_('Submit'), required=True, translate=True)
    logout_button_text = fields.Char(string="Logout Button Text", translate=True)

    frontend_validation = fields.Boolean(string="Frontend Validation", default=True,
                                         help="Enable JavaScript-Frontend-Form-Validation by jquery-validate!")

    snippet_area_top = fields.Html(string="Top Snippet Area", translate=True)
    snippet_area_bottom = fields.Html(string="Bottom Snippet Area", translate=True)

    # TODO: Add this to the <head> section of website.layout somehow :)
    custom_css = fields.Text(string="Custom CSS", help="TODO! This is not working yet!!!")

    # TODO: Add a user_group_ids and user_ids field to set what Users and or groups are allowed to view a form
    #       website. Make sure the controller then checks these groups correctly!
    #       Default should be the public user of the website so all are allowed to view/use the form by default

    clear_session_data_after_submit = fields.Boolean(string="Clear Form after Submit",
                                                     default=True,
                                                     help="If set the form will be empty again after a successful "
                                                          "submit!")

    # Edit existing record if logged in
    edit_existing_record_if_logged_in = fields.Boolean(string="Edit existing record if logged in",
                                                       help="If set and a user is logged in (e.g. by token) he can edit"
                                                            " one existing record related to model linked to the form."
                                                            " If the current form model is not res.partner or res.user"
                                                            " you can mark a res.partner or res.user many2one field of"
                                                            " the form as the login field. The record in the form-model"
                                                            " where the marked field matches the logged in user (or"
                                                            " the users partner) can than be edited.\n"
                                                            "Clear Session Data after Submit WILL NOT WORK if this"
                                                            " is set and a user is logged in!")

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
    redirect_after_submit = fields.Boolean(string="Redirect after successful submit!", default=True,
                                           oldname="thank_you_page_after_submit",
                                           help="Redirect after the successful submission of the form."
                                                "If not set the user will stay on the form page")
    # Technically this will pop the "clear_session_data" key from the form session data if set
    # so on the next hit the session data is still there and will not be removed!
    thank_you_page_edit_data_button = fields.Char(string="Edit Data Button", default=_('Edit'), translate=True,
                                                  help="If set a button will appear on the Thank You page to go "
                                                       "back to form to edit the data again!")
    thank_you_page_edit_redirect = fields.Char(string="Redirect URL after Edit on Thank You Page",
                                               help="If set the Edit Button will redirect to this page instead of"
                                                    "the regular form page!")
    thank_you_page_snippets = fields.Html(string="Thank you page", translate=True)

    website_url = fields.Char(compute="_cmp_website_url", string="Website URL")
    website_url_thanks = fields.Char(compute="_cmp_website_url_thanks", string="Website URL Thank you Page")

    # Login
    # -----
    login_required = fields.Boolean("Login required", help="If set you can only access the form if logged in.")
    show_token_login_form = fields.Boolean("Show Token Login Form",
                                           help="A form to enter the fs_ptoken will show up if not logged in when "
                                                "accessing the form!")

    # fs_ptoken login form
    tlf_top_snippets = fields.Html("TLF Top Snippets", help="Token Login Form Top Snippets", translate=True)
    tlf_headline = fields.Char("Token Login Form Headline", translate=True)
    tlf_label = fields.Char("Token Login Form Label", translate=True)
    tlf_submit_button = fields.Char("Token Login Form Submit Button", translate=True)
    tlf_logout_button = fields.Char("Token Login Form Logout Button", translate=True)
    tlf_bottom_snippets = fields.Html("TLF Bottom Snippets", translate=True, help="Token Login Form Top Snippets")

    @api.depends('name')
    def _cmp_website_url(self):
        for r in self:
            r.website_url = '/fso/form/'+str(r.id)

    @api.depends('name')
    def _cmp_website_url_thanks(self):
        for r in self:
            r.website_url_thanks = '/fso/form/thanks/'+str(r.id)

    @api.constrains('model_id', 'field_ids')
    def constrain_model_id_field_ids(self):
        for r in self:
            # Check all fields are fields of the current form_model
            if any(f.field_id.model_id != r.model_id for f in r.field_ids if f.field_id):
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

    @api.constrains('email_only', 'field_ids', 'confirmation_email_template', 'information_email_template',
                    'information_email_receipients')
    def constrain_emails(self):
        for r in self:
            if r.email_only:
                if not (r.information_email_template or r.confirmation_email_template):
                    raise ValidationError('E-Mail only forms require an e-mail template!')
                if r.information_email_template.auto_delete or r.confirmation_email_template.auto_delete:
                    raise ValidationError('E-Mail Template field "auto_delete" must be "False" for email only forms!')
            if r.information_email_template:
                if not r.information_email_receipients:
                    raise ValidationError('Information e-mail template is set but information email receipients are '
                                          'missing!')
                if not r.information_email_template.subject:
                    raise ValidationError('E-Mail subject is missing in information email template!')
                if r.information_email_template.model_id.id != r.model_id.id:
                    raise ValidationError('Information e-mail template model does not match the form model!')
            if r.confirmation_email_template:
                if not r.confirmation_email_template.subject:
                    raise ValidationError('E-Mail subject is missing in confirmation email template!')
                email_fields = [f for f in r.field_ids if f.confirmation_email]
                if not email_fields or len(email_fields) != 1:
                    raise ValidationError('Confirmation e-mail template is set but none or more than one field(s) '
                                          'are marked es confirmation email receiver!')
                if r.confirmation_email_template.model_id.id != r.model_id.id:
                    raise ValidationError('Confirmation e-mail template model does not match the form model!')

    # Remove noupdate for view auth_partner_form.meinedaten on addon update
    def init(self, cr, context=None):
        # Get all xml_ids for views and templates where the update would be prevented on addon install/update
        ir_model_data_obj = self.pool.get('ir.model.data')
        fso_forms_views_noupdate_ids = ir_model_data_obj.search(cr, SUPERUSER_ID,
                                                                [('module', '=', 'fso_forms'),
                                                                 ('model', '=', 'ir.ui.view'),
                                                                 ('noupdate', '=', True)
                                                                 ])
        if fso_forms_views_noupdate_ids:
            logger.warning('Views and or templates with noupdate found! %s' % fso_forms_views_noupdate_ids)
            logger.info('Removing noupdate from ir.model.data %s' % fso_forms_views_noupdate_ids)
            ir_model_data_records = ir_model_data_obj.browse(cr, SUPERUSER_ID, fso_forms_views_noupdate_ids)
            ir_model_data_records.write({"noupdate": False})


class FSONFormField(models.Model):
    _name = "fson.form_field"
    _order = 'sequence'

    _allowed_field_types = ['boolean', 'char', 'text', 'selection', 'many2one', 'date', 'integer', 'float', 'binary']
    _protected_fields = set(MAGIC_COLUMNS + ['parent_left', 'parent_right',
                                             'sosync_fs_id', 'sosync_write_date', 'sosync_synced_version'])
    _hpf_cls = 'hide_it'

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage', default=True)

    form_id = fields.Many2one(comodel_name="fson.form", string="Form", required=True,
                              index=True, ondelete='cascade')
    form_model_name = fields.Char(string="Form Model", related='form_id.model_id.model', help='Form Model name',
                                  readonly=True, store=True)
    # ATTENTION: The domain is computed dynamically in the onchange method!
    field_id = fields.Many2one(string="Field", comodel_name='ir.model.fields',
                               index=True, ondelete='cascade')
    field_ttype = fields.Selection(string="Field Type", related='field_id.ttype', help='ttype',
                                   readonly=True, store=True)
    field_model_name = fields.Char(string="Field Model", related='field_id.model_id.model', help='Model name',
                                   readonly=True, store=True)
    binary_name_field_id = fields.Many2one(string="File Name Field", comodel_name='ir.model.fields',
                                           domain="[('ttype','=','char'), "
                                                  " ('readonly','=',False), "
                                                  " ('name','not in',"+str(list(_protected_fields))+")]",
                                           index=True, ondelete='cascade')
    label = fields.Char(string='Label', translate=True)
    placeholder = fields.Char(string='Placeholder Text', translate=True,
                              help="This is the placeholder text that will be shown inside of the input fields!")
    yes_text = fields.Char(string="Yes Text", help="Only for radio-styled boolean fields!")
    no_text = fields.Char(string="No Text", help="Only for radio-styled boolean fields")
    mandatory = fields.Boolean(string='Mandatory', help="For boolean fields mandatory means you have to choose 'yes'"
                                                        "even if it is shown as a radio button!")
    nodata = fields.Boolean(string='Hide Data if logged in',
                            help='Do not show/pre-fill data in the website form if logged in.')
    readonly = fields.Boolean(string='Readonly if logged in',
                              help='Do not allow changing the data of the field if logged in and a record exits '
                                   'already! WARNING: This has NO effect if no record exists of no user is logged in!')
    login = fields.Boolean(string="Login Record", help="Only valid for many2one res.partner or res.user fields! "
                                                       "If set and the logged user relates to the partner or is the "
                                                       "user set in this field we try to load the corresponding record "
                                                       "and it's data to prefil the form and update the existing"
                                                       "record on form submit!")
    confirmation_email = fields.Boolean(string='Confirmation Email', help='Send a confirmation e-mail to this address')
    validation_rule = fields.Char(string='Frontend Validation', help="JQuery Frontend Validation Settings")
    css_classes = fields.Char(string='CSS classes', default='col-lg-6',
                              help="Besides Bootstrap classes you can use special fso-form-widget-* classes e.g.: "
                                   "for image previews 'fso-form-widget-image' or image icons 'fso-form-widget-icon'!")
    clearfix = fields.Boolean(string='Clearfix', help='Places a DIV box with .clearfix after this field')
    style = fields.Selection(selection=[('selection', 'Selection'),
                                        ('radio_selectnone', 'Radio + SelectNone'),
                                        ('radio', 'Radio')],
                             string='Field Style')
    force_selection = fields.Boolean(string="Force Selection", help="Forces a selection for radio and selection "
                                                                    "styled fields")
    information = fields.Html(string='Information', help='Information Text or Snippet Area if no field is selected!',
                              translate=True)

    default = fields.Char(string="Default", help="For Many2one fields simply use the id or the XMLID of the record")

    honeypot = fields.Boolean(string="Honeypot", help="This field is a honeypot field to detect SPAM. "
                                                      "It must be invisible in the form! If it is filled it means"
                                                      "that this was a bot and we can dismiss the form input!")

    # TODO: Add file type or mime type restrictions for binary fields
    #       HINT: check html  parameter 'accept' and 'type'

    @api.constrains('field_id', 'binary_name_field_id')
    def constrain_field_id(self):
        for r in self:
            if r.honeypot:
                if r.field_id:
                    raise ValidationError('You can not select a real field for a honeypot field!')
                if r.mandatory:
                    raise ValidationError('Honeypot fields must not be mandatory or the frontend validation will fail!')
                if self._hpf_cls not in r.css_classes:
                    raise ValidationError("The class %s is missing for a honey pot field!" % self._hpf_cls)
                if r.readonly:
                    raise ValidationError("Honeypot fields can not be readonly!")
                if r.default:
                    raise ValidationError("Honeypot fields can not have a default value!")
            if r.field_id:
                # Check readonly
                if r.field_id.readonly and r.show:
                    raise ValidationError('You can not add readonly fields that you show on the form!')
                # Check protected fields
                if r.field_id.name in self._protected_fields:
                    raise ValidationError('Protected and system fields are not allowed!')
                # Check field ttype
                if r.field_id.ttype not in self._allowed_field_types:
                    raise ValidationError('Field type %s is not supported in form fields!' % r.field_id.ttype)
                # Check required fields
                #if r.field_id.required and (not r.mandatory or not r.show):
                if r.field_id.required and not r.mandatory:
                    raise ValueError('System-Required fields must have show and mandatory set to True in the form!')
                # Check binary_name_field_id
                if r.field_id.ttype != 'binary' and r.binary_name_field_id:
                    raise ValueError('"File Name" field must be empty for non binary fields!')
                # Check login field
                if r.login:
                    if r.field_ttype != 'many2one':
                        raise ValueError('The login field must be of type "many2one"!')
                    if r.field_id.relation not in ['res.partner', 'res.user']:
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

    @api.onchange('show', 'mandatory', 'field_id', 'binary_name_field_id', 'login', 'honeypot')
    def oc_show(self):
        if not self.show:
            self.mandatory = False
        if self.field_id:
            if self.field_id.required:
                #self.show = True
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
        if self.honeypot:
            self.mandatory = False
            self.field_id = False
            self.nodata = False
            self.readonly = False
            self.login = False
            self.confirmation_email = False
            self.default = False
            if self._hpf_cls not in (self.css_classes or ''):
                self.css_classes = (self.css_classes or '') + ' ' + self._hpf_cls

    @api.onchange('style', 'mandatory')
    def oc_style(self):
        if self.style == 'radio_selectnone':
            self.mandatory = False

    @api.model
    def _field_id_domain(self):
        field_id_domain = [('ttype', 'in', self._allowed_field_types),
                           ('name', 'not in', list(self._protected_fields))]
        # Try to get the form model id
        try:
            if self.form_id and self.form_id.model_id:
                field_id_domain.append(('model_id', '=', self.form_id.model_id.id))
        except Exception as e:
            logger.warning('Could not set dynamic domain for field_id:\n%s' % repr(e))
            field_id_domain.append(('model_id', '=', False))
            pass
        return field_id_domain

    # Set the initial domain on 'view load' for field_id
    # DISABLED: Seems not to work for nested tree views in form views! We would need to create a tree view and use
    #           this for the one2many field 'field_ids' instead of a nested tree view in fson_form.xml
    # @api.model
    # def fields_view_get(self, view_id=None, view_type='tree', context=None, toolbar=False, submenu=False):
    #     context = context if context else {}
    #     result = super(FSONFormField, self).fields_view_get(view_id=view_id, view_type=view_type, context=context,
    #                                                         toolbar=toolbar, submenu=submenu)
    #
    #     if view_type == 'tree':
    #         # Get our domain filter
    #         # TODO: Maybe we need to get field values from the context ?
    #         field_id_domain_string = str(self._field_id_domain())
    #
    #         # Convert the view to an element tree object
    #         doc = etree.XML(result['arch'])
    #
    #         # Update the field with our domain filter
    #         for node in doc.xpath("//field[@name='field_id']"):
    #             node.set('domain', field_id_domain_string)
    #
    #         # Overwrite the view xml with our modified version
    #         result['arch'] = etree.tostring(doc)
    #
    #     return result

    # Set dynamic Domain for field_id if things like the form model changes
    @api.onchange('field_id', 'form_id', 'form_model_name')
    def oc_field_id_dynamic_domain(self):
        field_id_domain = self._field_id_domain()
        return {'domain': {'field_id': field_id_domain}}

    # TODO: Open the form view in edit mode
    @api.multi
    def button_open_field_form_view(self):
        # Open a form view
        ctx = self.env.context
        print ctx
        active_id = ctx.get('active_id', False)
        form_view = self.env.ref('fso_forms.fson_form_field_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Form Field',
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': form_view.id,
            #'context': ctx,
            # if you want to open the form in edit mode direclty
            'flags': {'initial_mode': 'edit', 'action_buttons': True},
            'target': 'new',
        }
