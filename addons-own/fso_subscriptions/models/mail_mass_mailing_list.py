# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class MailMassMailingList(models.Model):
    _inherit = "mail.mass_mailing.list"

    list_type = fields.Selection(string="Type", selection=[('email', "Email Subscription"),
                                                           ('frst_massmail', "Fundraising Studio Mailing"),
                                                           ('petition', "Petition"),
                                                           ('sms', 'SMS Subscription'),
                                                           ('whatsapp', "WhatsApp Subscription")],
                                 default='email')

    # TODO: APPROVAL FOR LIST CONTACTS
    # TODO: "Opt-Out" set and custom state for non approved list contacts if approval needed is set!
    # TODO: The approval fields should be added to an abstract model - to much code replication right now - we could
    #       add a class variable for the selection field e.g.: _bestaetigt_typ = [('doubleoptin', 'DoubleOptIn')]
    #       so we could "configure" this field by class if needed
    # TODO: Double-Opt-In E-Mail Template Many2One to email.template
    # TODO: Inverse Field(s) for many2one !!!
    bestaetigung_erforderlich = fields.Boolean("Approval needed",
                                               default=False,
                                               help="If this checkbox is set an E-Mail will be send to the"
                                                    "subscriber containing a link to confirm the subscription "
                                                    "(Double-Opt-In)")
    bestaetigung_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn')],
                                        string="Approval Type",
                                        default='doubleoptin')

    # SUBSCRIPTION FORM
    # TODO: Check all relevant settings of the subscription_form
    subscription_form = fields.Many2one(string="Subscription Form", comodel_name="fson.form",
                                        help="Set the subscription form for the model"
                                             "mail.mass_mailing.contact")

    # WEBPAGE
    website_url = fields.Char(compute="_cmp_website_url", string="Website URL", readonly=True)

    page_top = fields.Html(string="Top Snippets", help="Top Container for Snippets ", translate=True)
    page_left = fields.Html(string="Left Snippets", help="Main Container for Snippets", translate=True)
    page_bottom = fields.Html(string="Bottom Snippets", help="Bottom Container for Snippets", translate=True)

    page_top_classes = fields.Char(string="Top CSS Classes", default='col-sm-12, col-md-12 col-lg-12')
    page_left_classes = fields.Char(string="Left CSS Classes", default='col-sm-12, col-md-7 col-lg-7')
    page_right_classes = fields.Char(string="Right CSS Classes", default='col-sm-12, col-md-5 col-lg-5')
    page_bottom_classes = fields.Char(string="Bottom CSS Classes", default='col-sm-12, col-md-12 col-lg-12')

    # GOALS AND INFORMATION
    goal = fields.Integer(string="Subscription Goal")
    goal_reached = fields.Integer(compute="_cmp_goal_reached", string="Subscription reached",
                                  readonly=True, help="Subscriptions reached in %")
    goal_bar = fields.Boolean(string="Show Goal-Reached-Bar", default=True)
    goal_text = fields.Char(string="Goal Text", translate=True, default=_('Help us to reach'))
    goal_text_after = fields.Char(string="Goal Text After", translate=True, default=_('subscriptions!'))

    def _cmp_goal_reached(self):
        for r in self:
            if r.goal and r.contact_nbr:
                percentage_reached = int(round(float(r.contact_nbr) / (float(r.goal) / 100)))
                r.goal_reached = percentage_reached if percentage_reached <= 100 else 100
            else:
                r.goal_reached = 0

    def _cmp_website_url(self):
        for r in self:
            r.website_url = '/fso/subscription/'+str(r.id)

    @api.multi
    def create_subscription_form(self):
        for r in self:
            if not r.subscription_form:
                # Create the fso form
                list_contact_model = self.env['ir.model'].search([('model', '=', 'mail.mass_mailing.contact')])
                form_vals = {'name': 'Subscription form for mailing list %s (id %s)' % (r.name, r.id),
                             'model_id': list_contact_model.id,
                             'submit_button_text': 'Subscribe',
                             'clear_session_data_after_submit': False,
                             'edit_existing_record_if_logged_in': True,
                             'email_only': False,
                             'submission_url': '/fso/subscription/%s' % r.id}
                form = self.env['fson.form'].create(form_vals)

                # Create the fso form fields
                f_fields = {'firstname': {'sequence': 1,
                                          'label': 'Firstname',
                                          'mandatory': False,
                                          'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                          'clearfix': True},
                            'lastname': {'sequence': 2,
                                         'label': 'Lastname',
                                         'mandatory': True,
                                         'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                         'clearfix': True},
                            'email': {'sequence': 3,
                                      'label': 'E-Mail',
                                      'mandatory': True,
                                      'css_classes': 'col-sm-12 col-md-12 col-lg-12',
                                      'clearfix': True},
                            'list_id': {'sequence': 9999,
                                        'label': 'Subscription List',
                                        'default': r.id,
                                        'mandatory': True,
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
