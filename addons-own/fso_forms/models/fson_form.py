# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.tools import SUPERUSER_ID
from openerp.models import MAGIC_COLUMNS

from lxml import etree
import ast

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _name = "fson.form"

    _order = 'sequence'

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)

    type = fields.Selection(string='Type', selection=[('', 'No Type Set'), ('standard', 'Standard')],)

    name = fields.Char(string="Form Name", required=True)

    model_id = fields.Many2one(string="Model", comodel_name="ir.model", required=True)
    field_ids = fields.One2many(string="Fields", comodel_name="fson.form_field", inverse_name="form_id",
                                copy=True)

    create_as_user = fields.Many2one(string="Always create records as user", comodel_name="res.users",
                                     help="ALWAYS create new records with this user!")
    create_as_user_nologin = fields.Many2one(string="Create records if not logged in as user", comodel_name="res.users",
                                             help="Create new records with this user only if not logged in!")
    update_as_user = fields.Many2one(string="Always update records as user", comodel_name="res.users",
                                     help="ALWAYS update records with this user!")
    update_as_user_nologin = fields.Many2one(string="Update records if not logged in as user", comodel_name="res.users",
                                             help="Update records with this user only if not logged in!")

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
                                                  index=True,
                                                  copy=True)
    information_email_template = fields.Many2one(string='Information Email Template',
                                                 comodel_name='email.template',
                                                 inverse_name="information_email_template_fso_forms",
                                                 index=True,
                                                 copy=True)
    # TODO: Add an domain to only show partners with e-mails and no opt-out setting!
    information_email_receipients = fields.One2many(string='Information E-Mail Receipients',
                                                    comodel_name='res.partner',
                                                    inverse_name="information_email_receipient_fso_form",
                                                    copy=True)

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

    # Final Redirect URL
    # ------------------
    url_after_successful_form_submit = fields.Char(compute="_cmp_url_after_successful_form_submit",
                                                   string="Computed Redirect URL")

    @api.depends('name')
    def _cmp_website_url(self):
        for r in self:
            r.website_url = '/fso/form/'+str(r.id)

    @api.depends('name')
    def _cmp_website_url_thanks(self):
        for r in self:
            r.website_url_thanks = '/fso/form/thanks/'+str(r.id)

    @api.depends('redirect_after_submit', 'redirect_url_if_logged_in', 'redirect_url')
    def _cmp_url_after_successful_form_submit(self):
        for r in self:
            default_website_user = r.env.ref('base.public_user', raise_if_not_found=True)
            if not r.redirect_after_submit:
                r.url_after_successful_form_submit = r.website_url
            elif r.redirect_url_if_logged_in and r.env.user and default_website_user != r.env.user.id:
                r.url_after_successful_form_submit = r.redirect_url_if_logged_in
            elif r.redirect_url:
                r.url_after_successful_form_submit = r.redirect_url
            else:
                r.url_after_successful_form_submit = r.website_url_thanks

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

    # @api.model
    # def compute_type_if_not_set(self):
    #     type_missing = self.search([('type', '=', False)])
    #     logger.info("Found %s forms where type 'standard' is missing" % len(type_missing))
    #     type_missing.write({'type': 'standard'})

    @api.multi
    def button_open_form_page(self):
        self.ensure_one()
        active_form = self
        return {
            'name': _('Open Form Page'),
            'type': 'ir.actions.act_url',
            'res_model': 'ir.actions.act_url',
            'target': 'new',
            'url': active_form.website_url
        }

    @api.multi
    def button_open_redirect_page(self):
        self.ensure_one()
        active_form = self
        return {
            'name': _('Open Redirect Page'),
            'type': 'ir.actions.act_url',
            'res_model': 'ir.actions.act_url',
            'target': 'new',
            'url': active_form.url_after_successful_form_submit
        }
