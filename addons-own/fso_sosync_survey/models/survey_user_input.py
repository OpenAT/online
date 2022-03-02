# -*- coding: utf-8 -*-

from openerp import models, fields


class SurveyUserInputSosync(models.Model):
    _name = 'survey.user_input'
    _inherit = ['survey.user_input', 'base.sosync']

    partner_id = fields.Many2one(sosync="fson-to-frst")
    survey_id = fields.Many2one(sosync="fson-to-frst")
    state = fields.Selection(sosync="fson-to-frst")
    type = fields.Selection(sosync="fson-to-frst")
    quizz_score = fields.Float(sosync="fson-to-frst")
    test_entry = fields.Boolean(sosync="fson-to-frst")
