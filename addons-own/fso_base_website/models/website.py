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

    # @api.model
    # def _get_robots_view(self):
    #     return self.env.ref('fso_base_website.robots_txt_view')

    # robots_view_id = fields.Many2one(comodel_name="ir.ui.view", string="robots ir.ui.view id",
    #                                  default=lambda self: self.env.ref('fso_base_website.robots_txt_view'),
    #                                  readonly=True)
    # robots_view_arch_field = fields.Text(related="robots_view_id.arch", string="robots.txt")

    # New Solution
    robots_txt = fields.Text(string="robots.txt Extras",
                             help="Add custom instructions to the top of the robots.txt file!")

    # TODO: !!! USE LOWERCASE FIELD NAMES !!!
    PublicPartnerNoSubscribe = fields.Boolean(related="partner_id.no_subscribe",
                                              string="Public Partner: Do not add as follower")
    PublicPartnerTimezone = fields.Selection(related="partner_id.tz",
                                             string="Public Partner: Timezone")
    # END TODO

    google_analytics_script = fields.Text(string="Google Analytics Script")

