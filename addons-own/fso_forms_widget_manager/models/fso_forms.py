# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


class FSONForm(models.Model):
    _inherit = "fson.form"

    widget_manager_ids = fields.One2many(string='Widgets',
                                         comodel_name='website.widget_manager',
                                         compute="_compute_widget_manager_ids",
                                         readonly=True,
                                         translate=True)

    widget_manager_count = fields.Integer(string='Widgets Count',
                                          compute="_compute_widget_manager_count",
                                          readonly=True,
                                          translate=True)

    @api.multi
    @api.depends('name')
    def _compute_widget_manager_ids(self):
        widget_manager_obj = self.env['website.widget_manager']

        for r in self:
            search_params = [('source_page', '=like', '%' + r.website_url)]
            widget_manager_rec = widget_manager_obj.search(search_params)
            r.widget_manager_ids = widget_manager_rec

    @api.multi
    @api.depends('name')
    def _compute_widget_manager_count(self):
        for r in self:
            r.widget_manager_count = len(r.widget_manager_ids) or 0

    @api.multi
    def button_open_widget_manager(self):
        self.ensure_one()
        active_form = self
        return {
            'name': _('Widget Manager'),
            'type': 'ir.actions.act_window',
            'res_model': 'website.widget_manager',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('source_page', '=like', '%' + active_form.website_url)],
            'context': {'default_source_page': active_form.website_url}
        }
