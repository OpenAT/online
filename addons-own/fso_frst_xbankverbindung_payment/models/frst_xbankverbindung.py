# -*- coding: utf-8 -*-
from openerp import models, fields, api


import logging
logger = logging.getLogger(__name__)


class FRSTxBankverbindungPaymentAcquirer(models.Model):
    _inherit = "frst.xbankverbindung"

    acquirer_ids = fields.One2many(string='Payment Acquirer',
                                   comodel_name='payment.acquirer',
                                   inverse_name='frst_xbankverbindung_id')
