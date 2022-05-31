# -*- coding: utf-8 -*-
from openerp import models, fields


class SurveySurveyOptions(models.Model):
    _inherit = 'survey.survey'

    css_class = fields.Char(string="CSS class for survey")
    start_button_text = fields.Char(string="Start button text", translate=True)
