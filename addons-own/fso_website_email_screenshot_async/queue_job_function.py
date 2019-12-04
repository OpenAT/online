# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _

import logging
_log = logging.getLogger()


class JobFunction(models.Model):
    _inherit = 'queue.job.function'

    @api.model
    def set_fso_website_email_screenshot_async_channel(self):
        _log.info('Set correct channel "root.screenshot" for connector function "fso_website_email_screenshot_async"')

        # Setup the channel 'screenshot'
        screenshot_channel = self.env.ref('fso_website_email_screenshot_async.queue_job_channel_channel_screenshot',
                                           raise_if_not_found=False)
        if not screenshot_channel:
            channel_obj = self.env['queue.job.channel'].sudo()
            screenshot_channel = channel_obj.search([('name', '=', 'screenshot')])

            if not screenshot_channel:
                root_channel = channel_obj.search([('name', '=', 'root')])
                if len(root_channel) == 1:
                    screenshot_channel = channel_obj.create({'name': 'screenshot',
                                                             'parent_id': root_channel.id})

        # Setup the screenshot function
        screenshot_function = self.sudo().search([('name', '=like', '%fso_website_email_screenshot_async%')])
        if len(screenshot_function) == 1 and screenshot_channel and len(screenshot_channel) == 1:
            if screenshot_function.channel_id.id != screenshot_channel.id:
                screenshot_function.write({'channel_id': screenshot_channel.id})
