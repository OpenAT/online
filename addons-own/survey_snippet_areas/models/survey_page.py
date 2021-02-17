# -*- coding: utf-8 -*-
from openerp import models, fields


class SurveyPage(models.Model):
    _inherit = 'survey.page'

    snippets_top = fields.Html('Snippets Top')
    snippets_bottom = fields.Html('Snippets Bottom')
