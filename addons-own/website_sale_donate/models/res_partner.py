# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    giftee_sale_order_ids = fields.One2many(comodel_name='sale.order', inverse_name="giftee_partner_id",
                                            string="Gifting Sale Orders")
