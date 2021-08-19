# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.models import MAGIC_COLUMNS
from  openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class FSONFormField(models.Model):
    _name = "fson.form_field"
    _order = 'sequence'

    _allowed_field_types = ['boolean', 'char', 'text', 'selection', 'many2one', 'date', 'integer', 'float', 'binary']
    _protected_fields = set(MAGIC_COLUMNS + ['parent_left', 'parent_right',
                                             'sosync_fs_id', 'sosync_write_date', 'sosync_synced_version'])
    _hpf_cls = 'hide_it'

    type = fields.Selection(string="Type", selection=[('model', 'Model Field'),
                                                      ('honeypot', 'Honeypot Field'),
                                                      ('snippet_area', 'Snippet Area'),
                                                      ('mail_message', 'Comment / Note'),
                                                      ])
    mail_message_subtype = fields.Many2one(comodel_name='mail.message.subtype',
                                           string="Comment Subtype")

    sequence = fields.Integer('Sequence', help='Sequence number for ordering', default=1000)
    show = fields.Boolean(string='Show', help='Show field in webpage', default=True)

    form_id = fields.Many2one(comodel_name="fson.form", string="Form", required=True,
                              index=True, ondelete='cascade')
    form_model_name = fields.Char(string="Form Model", related='form_id.model_id.model', help='Form Model name',
                                  readonly=True, store=True)
    # ATTENTION: The domain is computed dynamically in the onchange method!
    field_id = fields.Many2one(string="Model-Field", comodel_name='ir.model.fields',
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
    clearfix = fields.Boolean(string='Linebreak', help='Places a DIV box with .clearfix after this field')
    style = fields.Selection(selection=[('selection', 'Selection'),
                                        ('radio_selectnone', 'Radio + SelectNone'),
                                        ('radio', 'Radio')],
                             string='Field Style')
    force_selection = fields.Boolean(string="Force Selection", help="Forces a selection for radio and selection "
                                                                    "styled fields")
    information = fields.Html(string='Information', help='Information Text or Snippet Area if no field is selected!',
                              translate=True)

    default = fields.Char(string="Default Field Value",
                          help="For Many2one or selection fields please use the id or the XMLID of the target-record."
                               "This can also be used with 'hidden' fields to enforce a value for a field!")

    domain = fields.Char(string="Search-Domain for Many2one Fields",
                         help="For Many2one fields to limit the available records to choose from")

    honeypot = fields.Boolean(string="Honeypot", help="DEPRECATED! use type='honeypot' instead!"
                                                      "This field is a honeypot field to detect SPAM. "
                                                      "It must be invisible in the form! If it is filled it means"
                                                      "that this was a bot and we can dismiss the form input!")

    @api.model
    def form_field_name(self):
        self.ensure_one()
        form_field = self
        if self.type == 'model':
            f_name = form_field.field_id.name
        elif self.type == 'honeypot':
            f_name = "hpf-%s" % form_field.id
        elif self.type == 'snippet_area':
            f_name = "snippet-area-field-%s" % form_field.id
        elif self.type == 'mail_message':
            f_name = "comment-field-%s" % form_field.id
        else:
            raise ValueError("FS-Online Form-Field-Type %s is not supported" % form_field.type)
        return f_name

    # TODO: Add file type or mime type restrictions for binary fields
    #       HINT: check html  parameter 'accept' and 'type'
    @api.constrains('field_id', 'binary_name_field_id', 'type', 'mandatory', 'readonly', 'default', 'show', 'login',
                    'binary_name_field_id', 'information', 'mail_message_subtype')
    def constrain_field_id(self):
        for r in self:
            # comment (mail_message) field
            if r.type == 'mail_message':
                if not r.mail_message_subtype:
                    raise ValidationError('Fields of type mail_message require a mail message subtype!')
                if r.mail_message_subtype.res_model \
                        and r.mail_message_subtype.res_model not in [r.form_model_name, 'fson.form']:
                    raise ValidationError('The mail_message_subtype.res_model is not suitable for this form model!')

            # honeypot field
            if r.type == 'honeypot':
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

            # model field
            if r.field_id:
                # Check type
                if r.type != "model":
                    raise ValidationError("The field type must be 'model' if a model field is set!")
                # Check readonly
                if not r.default and r.field_id.readonly and r.show:
                    raise ValidationError('You can not add readonly fields that you show on the form! %s' % r.field_id)
                # Check protected fields
                if r.field_id.name in self._protected_fields:
                    raise ValidationError('Protected and system fields are not allowed! %s' % r.field_id)
                # Check field ttype
                if r.field_id.ttype not in self._allowed_field_types:
                    raise ValidationError('Field type %s is not supported in form fields!' % r.field_id.ttype)
                # Check required fields
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
                # Check if style and force_selection attributes are allowed
                if r.field_id.ttype not in ['selection', 'many2one', 'boolean']:
                    if r.style:
                        raise ValidationError(
                            "style can only be set for fields of type 'selection', 'many2one' or 'boolean'")
                    if r.force_selection:
                        raise ValidationError(
                            "force_selection can only be set for fields of type 'selection', 'many2one' or 'boolean'")

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
                    raise ValueError("Required fields must have 'show' and 'mandatory' set to True in the form!")

            # snippet area
            if r.type == 'snippet_area':
                if r.field_id:
                    raise ValidationError("Please remove the 'model field' for snippet area fields!")

    @api.onchange('default')
    def onchange_default(self):
        if self.default and self.field_id.ttype == 'many2one' and not self.domain:
            return {'warning': {
                'title': _('Warning'),
                'message': _('Please make sure a search-domain is set if you set a default value for a Many2One'
                             'field!\n\nOtherwise the default value may not be in the selectable values for the'
                             'field because the Many2One values are limited to the first 200 results!')
            }}

    @api.onchange('show', 'mandatory', 'field_id', 'binary_name_field_id', 'login', 'honeypot', 'type', 'style',
                  'css_classes')
    def oc_show(self):
        if not self.show:
            self.mandatory = False
        # Model field
        if self.field_id:
            if not self.type == 'model':
                self.type = 'model'
            if self.field_id.required:
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
        # Honeypot field
        if self.type == 'honeypot':
            self.mandatory = False
            self.field_id = False
            self.nodata = False
            self.readonly = False
            self.login = False
            self.confirmation_email = False
            self.default = False
            self.information = False
            self.validation_rule = False
            self.style = False
            self.force_selection = False
            if self._hpf_cls not in (self.css_classes or ''):
                self.css_classes = (self.css_classes or '') + ' ' + self._hpf_cls
        # Snippet Area
        if self.type == 'snippet_area':
            self.mandatory = False
            self.field_id = False
            self.nodata = False
            self.readonly = False
            self.login = False
            self.confirmation_email = False
            self.default = False
            self.information = False
            self.validation_rule = False
            self.style = False
            self.force_selection = False

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
        # active_id = ctx.get('active_id', False)
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
            # if you want to open the form in edit mode directly
            #'flags': {'initial_mode': 'edit', 'action_buttons': True},
            'flags': {'action_buttons': True},
            'target': 'new',
        }

    @api.model
    def compute_type_if_not_set(self):
        model = self.search([('type', '=', False), ('field_id', '!=', False)])
        logger.info("Found %s fson form fields where type 'model' is missing" % len(model))
        model.write({'type': 'model'})

        honeypot = self.search([('type', '=', False), ('honeypot', '=', True)])
        logger.info("Found %s fson form fields where type 'honeypot' is missing" % len(honeypot))
        honeypot.write({'type': 'honeypot'})

        snippet_area = self.search([('type', '=', False), ('field_id', '=', False), ('honeypot', '=', False)])
        logger.info("Found %s fson form fields where type 'snippet_area' is missing" % len(snippet_area))
        snippet_area.write({'type': 'snippet_area'})
