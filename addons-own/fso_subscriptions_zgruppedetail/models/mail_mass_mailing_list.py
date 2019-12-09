# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class MailMassMailingList(models.Model):
    _inherit = "mail.mass_mailing.list"

    zgruppedetail_id = fields.Many2one(string="ZGruppeDetail", comodel_name='frst.zgruppedetail',
                                       inverse_name='mass_mailing_list_ids',
                                       help="Create PersonEmailGruppe records and vice versa for list contacts "
                                            "of this mailing list")
