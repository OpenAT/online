# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _

import logging
_log = logging.getLogger()


class JobFunction(models.Model):
    _inherit = 'queue.job.function'

    @api.model
    def set_fso_sosync_async_channel(self):
        _log.info('Set correct channel "root.sosync" for connector function "fso_sosync_async"')

        # Setup the channel 'screenshot'
        sosync_channel = self.env.ref('fso_sosync_async.queue_job_channel_channel_sosync',
                                      raise_if_not_found=False)
        if not sosync_channel:
            channel_obj = self.env['queue.job.channel'].sudo()
            sosync_channel = channel_obj.search([('name', '=', 'sosync')])

            if not sosync_channel:
                root_channel = channel_obj.search([('name', '=', 'root')])
                if len(root_channel) == 1:
                    sosync_channel = channel_obj.create({'name': 'sosync',
                                                         'parent_id': root_channel.id})

        # Setup the screenshot function
        sosync_function = self.sudo().search([('name', '=like', '%fso_sosync_async%')])
        if len(sosync_function) == 1 and sosync_channel and len(sosync_channel) == 1:
            if sosync_function.channel_id.id != sosync_channel.id:
                sosync_function.write({'channel_id': sosync_channel.id})
