# -*- coding: utf-8 -*-
from openerp.addons.fso_forms.controllers.controller import FsoForms
from openerp.http import request


class FsoFormsSurvey(FsoForms):
    # TODO: _redirect_after_form_submit ... and decide
    def _redirect_after_form_submit(self, form, record, forced_redirect_url='', forced_redirect_target=''):
        
        # Check if the form should redirect to a survey
        if not forced_redirect_url and form.redirect_after_submit and form.redirect_survey_id:

            survey_user_input_vals = {'survey_id': form.redirect_survey_id.id,
                                      'fson_form_id': form.id}

            # TODO: search for existing survey user input object of this form to continue with survey
            #       instead of always creating a new survey user input.

            # Add partner to survey user input if possible
            # --------------------------------------------
            survey_partner = None

            # res.partner form
            if form.model_id.model == 'res.partner' and record and record._name == 'res.partner':
                survey_partner = record
            # user is logged in
            elif self.is_logged_in():
                survey_partner = request.env.user.partner_id

            # Add the partner to the survey_user_input_vals
            if survey_partner:
                survey_user_input_vals['partner_id'] = survey_partner.id

            # Create the survey user input record
            # -----------------------------------
            survey_user_input = request.env['survey.user_input'].sudo().create(survey_user_input_vals)

            # Force the redirect url to the survey start page with the correct survey user input token
            # ----------------------------------------------------------------------------------------
            if form.survey_start_directly:
                forced_redirect_url = '/survey/fill/%s/%s' % (form.redirect_survey_id.id, survey_user_input.token)
            else:
                forced_redirect_url = '/survey/start/%s/%s' % (form.redirect_survey_id.id, survey_user_input.token)
            forced_redirect_target = form.redirect_survey_target

        # Return _redirect_after_form_submit
        return super(FsoFormsSurvey, self)._redirect_after_form_submit(
            form, record, forced_redirect_url=forced_redirect_url, forced_redirect_target=forced_redirect_target)

