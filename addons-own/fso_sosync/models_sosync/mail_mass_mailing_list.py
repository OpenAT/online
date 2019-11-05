# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class MailMassMailingListSosync(models.Model):
    _name = "mail.mass_mailing.list"
    _inherit = ["mail.mass_mailing.list", "base.sosync"]

    # contact_ids = fields.One2many(sosync="True")  # Inverse field not needed for sosyncer

    name = fields.Char(sosync="True")
    list_type = fields.Selection(sosync="True")

    website_published = fields.Boolean(sosync="True")
    system_list = fields.Boolean(sosync="True")

    partner_mandatory = fields.Boolean(sosync="True")

    bestaetigung_erforderlich = fields.Boolean(sosync="True")
    bestaetigung_typ = fields.Selection(sosync="True")

    # SUBSCRIPTION FORM
    # subscription_form = fields.Many2one(sosync="True")    # fso_forms is not in sync yet

    # GOALS AND INFORMATION
    goal = fields.Integer(sosync="True")
    goal_dynamic = fields.Integer(sosync="True")

