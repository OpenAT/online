# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    ## This file was never imported, so the commented column was never actually
    ## added. Since the file is added now, the column is removed.
    # giftee_sale_order_ids = fields.One2many(comodel_name='sale.order', inverse_name="giftee_partner_id",
    #                                         string="Gifting Sale Orders")

    # Honey pot field to be used with website wide forms
    honey_pot_field = fields.Char(string='Honey pot field')
