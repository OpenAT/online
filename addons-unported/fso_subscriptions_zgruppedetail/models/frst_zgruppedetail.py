# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


# Fundraising Studio groups
class FRSTzGruppeDetail(models.Model):
    _inherit = "frst.zgruppedetail"

    mass_mailing_list_ids = fields.One2many(string="Mailing Lists",
                                            comodel_name='mail.mass_mailing.list',
                                            inverse_name='zgruppedetail_id',
                                            readonly=True)
