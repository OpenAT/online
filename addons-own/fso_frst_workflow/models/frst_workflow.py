# -*- coding: utf-8 -*-

from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class FRSTWorkflow(models.Model):
    _inherit = 'frst.workflow'

    name = fields.Char(string="Name")
