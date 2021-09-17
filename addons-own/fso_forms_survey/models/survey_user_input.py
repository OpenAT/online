# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    fson_form_id = fields.Many2one(comodel_name="fson.form", inverse_name="survey_result_ids",
                                   string="FS-Online Form Origin")
