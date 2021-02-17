# -*- coding: utf-8 -*-
from openerp.addons.survey.controllers.main import WebsiteSurvey
from openerp import http
from openerp.http import request


class WebsiteSurveyCustomThankYouPage(WebsiteSurvey):

    @http.route()
    def fill_survey(self, survey, token, prev=None, **post):
        res = super(WebsiteSurveyCustomThankYouPage, self).fill_survey(survey, token, prev=prev, **post)

        # TODO: Check if res would render the template 'survey.sfinished' and
        #       replace it with the template 'survey_thank_you_page.sfinished_custom' if 'blank_thank_you_page'
        #       is set in the survey

        if hasattr(res, 'template') and res.template == 'survey.sfinished':
            if hasattr(res, 'qcontext'):
                survey = res.qcontext.get('survey', None)
                if survey:
                    if survey.thank_you_url:
                        return request.redirect(survey.thank_you_url)
                    if survey.blank_thank_you_page:
                        return request.website.render('survey_thank_you_page.sfinished_custom', res.qcontext)

        return res
