# -*- coding: utf-'8' "-*-"
from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class ResCompanySosyncSettings(models.Model):
    _inherit = "res.company"

    # Job submission url overwrite for debugging purposes
    sosync_job_submission_url = fields.Char(string="sosync job sumission URL",
                                            help="Overwrite for the sosync job submission URL. "
                                                 "Keep empty for default URL!")
