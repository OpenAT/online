# -*- coding: utf-8 -*-

from openerp import models, fields


class SurveyUserInputLineSosync(models.Model):
    _name = 'survey.user_input_line'
    _inherit = ['survey.user_input_line', 'base.sosync']

    question_id = fields.Many2one(sosync="fson-to-frst")
    quizz_mark = fields.Float(sosync="fson-to-frst")
    answer_type = fields.Selection(sosync="fson-to-frst")
    skipped = fields.Boolean(sosync="fson-to-frst")
    value_date = fields.Datetime(sosync="fson-to-frst")
    value_free_text = fields.Text(sosync="fson-to-frst")
    value_number = fields.Float(sosync="fson-to-frst")
    value_suggested = fields.Many2one(sosync="fson-to-frst")
    value_suggested_row = fields.Many2one(sosync="fson-to-frst")
    value_text = fields.Char(sosync="fson-to-frst")
