# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID

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

    # Approval for list contacts
    # TODO: The approval fields should be added to an abstract model - to much code replication right now - we could
    #       add a class variable for the selection field e.g.: _bestaetigt_typ = [('doubleoptin', 'DoubleOptIn')]
    #       so we could "configure" this field by class if needed
    bestaetigung_erforderlich = fields.Boolean("Approval needed",
                                               default=False,
                                               help="If this checkbox is set an E-Mail will be send to the"
                                                    "subscriber containing a link to confirm the subscription "
                                                    "(Double-Opt-In)")
    bestaetigung_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn')],
                                        string="Approval Type",
                                        default='doubleoptin')
    # TODO: Double-Opt-In E-Mail Template Many2One to email.template

    # Subscription Goal
    subscription_goal = fields.Integer(string="Subscription Goal")

    # Webpage
    subscription_page = fields.Html(string="Subscription Page", help="Main Container for Snippets")
    subscription_page_top = fields.Html(string="Subscription Page Top", help="Top Container for Snippets ")
    subscription_page_bottom = fields.Html(string="Subscription Page Bottom", help="Bottom Container for Snippets")


    # Optional: Custom Subscription Form
    # TODO: Check all relevant settings of the subscription_form
    subscription_form = fields.Many2one(string="Subscription Form", comodel_name="fson.form",
                                        help="Set the subscription form for the model"
                                             "mail.mass_mailing.contact")


