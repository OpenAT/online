# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _inherit = "fson.form"

    redirect_survey_id = fields.Many2one(comodel_name="survey.survey", inverse_name="fson_form_id",
                                      string="Redirect to Survey",
                                      help="Open survey after successful form submit")
    redirect_survey_target = fields.Selection(selection=[('_parent', '_parent'),
                                                         ('_blank', '_blank')],
                                              string="Survey Redirect target")

    survey_result_ids = fields.One2many(comodel_name="survey.user_input", inverse_name="fson_form_id",
                                        string="Survey Results")

    survey_total = fields.Integer(string="Survey Results Total", compute="compute_survey_total")

    # @api.constrains('redirect_survey_id', 'redirect_url', 'redirect_url_target', 'redirect_url_if_logged_in',
    #                 'redirect_url_if_logged_in_target')
    # def constrain_redirect_urls(self):
    #     for r in self:
    #         if r.redirect_survey_id:
    #             f_empty = ['redirect_url', 'redirect_url_target', 'redirect_url_if_logged_in',
    #                        'redirect_url_if_logged_in_target']
    #             if any(r[f] for f in f_empty):
    #                 raise ValidationError(_("If a survey is set as the redirect target the fields %s must"
    #                                         "be empty because they have no effect!") % f_empty)

    @api.constrains('redirect_survey_id', 'redirect_after_submit')
    def constrain_redirect_survey(self):
        for r in self:
            if r.type == 'standard' and r.redirect_survey_id:
                if not r.redirect_after_submit:
                    raise ValidationError("'redirect_survey_id' has no effect if 'redirect_after_submit' is not set! "
                                          "Therefore it must be empty or you may enable 'redirect_after_submit'.")

    @api.depends('redirect_after_submit', 'redirect_url_if_logged_in', 'redirect_url', 'redirect_survey_id')
    def _cmp_url_after_successful_form_submit(self):
        for r in self:
            if r.redirect_after_submit and r.redirect_survey_id:
                r.url_after_successful_form_submit = "/survey/start/%s" % r.redirect_survey_id.id
            else:
                super(FSONForm, self)._cmp_url_after_successful_form_submit()

    @api.depends('survey_result_ids')
    def compute_survey_total(self):
        for r in self:
            r.survey_total = len(r.survey_result_ids) if r.survey_result_ids else 0

    @api.multi
    def button_open_survey_results(self):
        self.ensure_one()
        active_form = self
        return {
            'name': _('Survey Results'),
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('fson_form_id', '=', active_form.id)],
            'context': {'default_fson_form_id': active_form.id}
        }
