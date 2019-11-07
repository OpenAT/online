# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class MailMassMailingList(models.Model):
    _inherit = "mail.mass_mailing.list"

    # Inverse field for list contacts (seems to be missing in original model)
    contact_ids = fields.One2many(comodel_name='mail.mass_mailing.contact', inverse_name="list_id",
                                  string="List Contacts")

    list_type = fields.Selection(string="Type", selection=[('email', "Email Subscription"),
                                                           ('frst_massmail', "Fundraising Studio Mailing"),
                                                           ('petition', "Petition"),
                                                           ('sms', 'SMS Subscription'),
                                                           ('whatsapp', "WhatsApp Subscription"),
                                                           ('none', "None")],
                                 default='email', required=True)

    website_published = fields.Boolean(string="View in Subscription Manager",
                                       help="If set the list will show up in the subscription manager")
    system_list = fields.Boolean(string="System List", readonly=True,
                                 help="System list are available to all installations and can not be removed!")

    # APPROVAL
    bestaetigung_erforderlich = fields.Boolean("Approval needed",
                                               default=True,
                                               help="If this checkbox is set an E-Mail will be send to the"
                                                    "subscriber containing a link to confirm the subscription "
                                                    "(Double-Opt-In)")
    bestaetigung_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn')],
                                        string="Approval Type",
                                        default='doubleoptin')

    # SUBSCRIPTION FORM
    # TODO: Check all relevant settings of the subscription_form (api.constrains)
    subscription_form = fields.Many2one(string="Subscription Form", comodel_name="fson.form",
                                        help="Set the subscription form for the model"
                                             "mail.mass_mailing.contact")

    # WEBPAGE
    website_url = fields.Char(compute="_cmp_website_url", string="Website URL", readonly=True)
    website_url_form = fields.Char(related="subscription_form.website_url",
                                   string="Form Website URL", readonly=True)
    website_url_form_thanks = fields.Char(related="subscription_form.website_url_thanks",
                                          string="Form Thank You Page", readonly=True)

    page_top = fields.Html(string="Top Snippets", help="Top Container for Snippets ", translate=True)
    page_left = fields.Html(string="Left Snippets", help="Main Container for Snippets", translate=True)
    page_bottom = fields.Html(string="Bottom Snippets", help="Bottom Container for Snippets", translate=True)

    page_top_classes = fields.Char(string="Top CSS Classes", default='col-sm-12, col-md-12 col-lg-12')
    page_left_classes = fields.Char(string="Left CSS Classes", default='col-sm-12, col-md-7 col-lg-7')
    page_right_classes = fields.Char(string="Right CSS Classes", default='col-sm-12, col-md-5 col-lg-5')
    page_bottom_classes = fields.Char(string="Bottom CSS Classes", default='col-sm-12, col-md-12 col-lg-12')

    # GOALS AND INFORMATION
    goal = fields.Integer(string="Subscription Goal")
    goal_dynamic = fields.Integer(compute="_cmp_goal_reached", store=True,
                                  string="Dynamic Subscription Goal")
    goal_increase_at = fields.Integer(string="Increase Goal at %",
                                      help="Increase the goal_dynamic with goal_increase_step at goal_reached")
    goal_increase_step = fields.Integer(string="Increase Goal Step")
    goal_reached = fields.Integer(compute="_cmp_goal_reached", store=True,
                                  string="Subscription reached %",
                                  readonly=True, help="Subscriptions reached in %")
    goal_bar = fields.Boolean(string="Show Goal-Reached-Bar", default=True)
    goal_text = fields.Char(string="Goal Text", translate=True, default=_('Help us to reach'))
    goal_text_after = fields.Char(string="Goal Text After", translate=True, default=_('subscriptions!'))

    @api.depends('goal', 'goal_increase_at', 'contact_ids')
    def _cmp_goal_reached(self):
        for r in self:
            if r.goal and r.contact_nbr:

                # Initialize dynamic goal
                goal_dynamic = r.goal_dynamic if r.goal_dynamic else r.goal

                # Number of subscriptions (int)
                contact_nbr = r.contact_nbr

                def pr(subscribers, goal):
                    return int(round(float(subscribers) / (float(goal) / 100)))

                # Compute percentage reached based on list subscriptions
                percentage_reached = pr(contact_nbr, goal_dynamic)

                # Compute new dynamic goal and percentage_reached
                runs = 1
                while r.goal_increase_step and percentage_reached >= r.goal_increase_at:
                    goal_dynamic = goal_dynamic + r.goal_increase_step
                    percentage_reached = pr(contact_nbr, goal_dynamic)
                    runs = runs + 1
                    if runs > 100:
                        logger.error("goal_dynamic still not high enough after 100 increments!")
                        break

                r.goal_dynamic = goal_dynamic
                r.goal_reached = percentage_reached
            else:
                r.goal_reached = 0

    def _cmp_website_url(self):
        for r in self:
            r.website_url = '/fso/subscription/'+str(r.id)

    @api.constrains('list_type', 'partner_mandatory')
    def _constraint_partner_mandatory(self):
        for r in self:
            if r.list_type != 'none' and not r.partner_mandatory:
                raise AssertionError(_("If you select a list type other than 'none', 'partner mandatory' must be set!"))

    @api.constrains('goal', 'goal_dynamic', 'goal_increase_at', 'goal_increase_step')
    def _constraint_goal(self):
        for r in self:
            all_or_none_set = ['goal_increase_at', 'goal_increase_step']
            if any(r[f] for f in all_or_none_set):
                assert(all(r[f] for f in all_or_none_set)), _(
                    "You must set all or none of %s") % all_or_none_set
            if r.goal_increase_at and not (9 < r.goal_increase_at < 121):
                raise AssertionError(_('goal_increase_at must be between 10 and 120'))
            if r.goal_increase_step and r.goal_increase_step < 1:
                raise AssertionError(_('goal_increase_step must be 1 or more'))
            if r.goal and r.goal < 0:
                raise AssertionError(_('goal can not be negative'))
            if r.goal_dynamic:
                if r.goal_dynamic < 0:
                    raise AssertionError(_('goal_dynamic can not be negative'))

    @api.multi
    def create_subscription_form(self):
        for r in self:
            if not r.subscription_form:
                # Create the fso form
                list_contact_model = self.env['ir.model'].search([('model', '=', 'mail.mass_mailing.contact')])
                form_vals = {'name': _('Subscription form for mailing list %s (id %s)') % (r.name, r.id),
                             'model_id': list_contact_model.id,
                             'submit_button_text': _('Subscribe'),
                             'clear_session_data_after_submit': True,
                             'edit_existing_record_if_logged_in': True,
                             'email_only': False,
                             'thank_you_page_edit_data_button': False,
                             'thank_you_page_edit_redirect': '/fso/subscription/%s' % r.id,
                             'submission_url': '/fso/subscription/%s' % r.id}
                form = self.env['fson.form'].create(form_vals)

                # Create the fso form fields
                f_fields = {'firstname': {'sequence': 1,
                                          'show': True,
                                          'label': _('Firstname'),
                                          'mandatory': False,
                                          'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                          'clearfix': True},
                            'lastname': {'sequence': 2,
                                         'show': True,
                                         'label': _('Lastname'),
                                         'mandatory': True,
                                         'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                         'clearfix': True},
                            'email': {'sequence': 3,
                                      'label': _('E-Mail'),
                                      'show': True,
                                      'mandatory': True,
                                      'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                      'clearfix': True},
                            'list_id': {'sequence': 9900,
                                        'show': True,
                                        'label': _('Subscription List'),
                                        'default': r.id,
                                        'mandatory': True,
                                        'css_classes': 'hide_it'},
                            'partner_id': {'sequence': 9910,
                                           'show': False,
                                           'login': True,
                                           'label': _('Partner'),
                                           'mandatory': False,
                                           'css_classes': 'hide_it'},
                            'origin': {'sequence': 9920,
                                       'show': True,
                                       'label': _('Origin'),
                                       'default': r.website_url,
                                       'mandatory': False,
                                       'css_classes': 'hide_it'},
                            }
                fields_obj = self.env['ir.model.fields']
                form_field_obj = self.env['fson.form_field']
                for f, vals in f_fields.iteritems():
                    vals['form_id'] = form.id
                    vals['field_id'] = fields_obj.search([('model_id', '=', list_contact_model.id),
                                                          ('name', '=', f)]).id
                    form_field_obj.create(vals)

                # Add this form to the record
                r.write({'subscription_form': form.id})
