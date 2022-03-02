# -*- coding: utf-8 -*-

from openerp import models, fields


class SurveySurveySosync(models.Model):
    _name = 'survey.survey'
    _inherit = ['survey.survey', 'base.sosync']

    title = fields.Char(sosync="fson-to-frst")
    description = fields.Char(sosync="fson-to-frst")

