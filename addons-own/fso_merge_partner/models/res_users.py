# -*- coding: utf-8 -*-
from openerp import models, api
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class ResUsersFSOMerge(models.Model):
    _name = "res.users"
    _inherit = ["res.users", "fso.merge"]

