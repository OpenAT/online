# -*- coding: utf-8 -*-
from openerp import models, fields, api


# HINT: odoo/addons/website/models/res_config.py
# class WebsiteConfigSettings(models.Model):
#     _inherit = 'website.config.settings'
#
#     @api.model
#     def _get_robots_view(self):
#         robots_view = self.env['ir.ui.view'].sudo().search([('name', '=', 'website.robots')
#                                                             ])[0]
#         return robots_view
#
#     RobotsViewId = fields.Many2one(comodel_name="ir.ui.view", string="robots.txt id",
#                                    default=_get_robots_view, readonly=True)
#     RobotsArch = fields.Text(related="RobotsViewId.arch", string="robots.txt")


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def _get_robots_view(self):
        return self.env.ref('website.robots')

    RobotsViewId = fields.Many2one(comodel_name="ir.ui.view", string="robots.txt id", default=_get_robots_view,
                                   readonly=True)
    RobotsArch = fields.Text(related="RobotsViewId.arch", string="robots.txt")

    PublicPartnerNoSubscribe = fields.Boolean(related="partner_id.no_subscribe",
                                              string="Public Partner: Do not add as follower")
    PublicPartnerTimezone = fields.Selection(related="partner_id.tz",
                                             string="Public Partner: Timezone")

    google_analytics_script = fields.Text(string="Google Analytics Script")
