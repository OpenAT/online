# -*- coding: utf-8 -*-
from openerp import models, fields


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    blank_thank_you_page = fields.Boolean('Blank Thank You Page',
                                           help="Will show an empty Thank-You page to be designed with snippets instead"
                                                "of the default one")
    thank_you_url = fields.Char('Thank You Page Redirect-URL', help="Will use redirect to this url when the"
                                                                    "survey is done instead of the default"
                                                                    "thank you page")