# -*- coding: utf-8 -*-

from openerp import models, fields


class SurveyQuestionSosync(models.Model):
    _name = 'survey.question'
    _inherit = ['survey.question', 'base.sosync']

    survey_id = fields.Many2one(sosync="fson-to-frst")
    question = fields.Char(sosync="fson-to-frst")
    sequence = fields.Integer(sosync="fson-to-frst")
    type = fields.Selection(sosync="fson-to-frst")
