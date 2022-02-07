# -*- coding: utf-8 -*-
from openerp import models, fields, api


import logging
logger = logging.getLogger(__name__)


class PaymentAcquirerBank(models.Model):
    _inherit = "payment.acquirer"

    frst_xbankverbindung_id = fields.Many2one(string="xBankverbindung",
                                              comodel_name="frst.xbankverbindung")
