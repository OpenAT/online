# -*- coding: utf-8 -*-
from openerp import models, fields, api


import logging
logger = logging.getLogger(__name__)


class PaymentAcquirerBankSosync(models.Model):
    _name = "payment.acquirer"
    _inherit = ["payment.acquirer", "base.sosync"]

    frst_xbankverbindung_id = fields.Many2one(sosync="fson-to-frst")
