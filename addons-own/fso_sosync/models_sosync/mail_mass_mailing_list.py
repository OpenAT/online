# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class MailMassMailingListSosync(models.Model):
    _name = "mail.mass_mailing.list"
    _inherit = ["mail.mass_mailing.list", "base.sosync"]

    name = fields.Char(sosync="True")
    list_type = fields.Selection(sosync="True")

    partner_mandatory = fields.Boolean(sosync="True")

    bestaetigung_erforderlich = fields.Boolean(sosync="True")
    bestaetigung_typ = fields.Selection(sosync="True")

    # SUBSCRIPTION FORM
    # subscription_form = fields.Many2one(sosync="True")

    # GOALS AND INFORMATION
    goal = fields.Integer(sosync="True")

