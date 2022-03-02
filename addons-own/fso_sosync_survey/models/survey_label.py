# -*- coding: utf-8 -*-

from openerp import models, fields


class SurveyLabelSosync(models.Model):
    _name = 'survey.label'
    _inherit = ['survey.label', 'base.sosync']

    qestion_id = fields.Many2one(sosync="fson-to-frst")
    value = fields.Char(sosync="fson-to-frst")
    sequence = fields.Integer(sosync="fson-to-frst")
    quizz_mark = fields.Float(sosync="fson-to-frst")
