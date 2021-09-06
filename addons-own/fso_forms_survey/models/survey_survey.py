# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    fson_form_id = fields.One2many(comodel_name="fson.form", inverse_name="redirect_survey_id",
                                   string="FS-Online Forms",
                                   help="FS-Online Forms that start this survey after successful form submit")
