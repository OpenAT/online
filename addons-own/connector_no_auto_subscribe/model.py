# -*- coding: utf-8 -*-
from openerp import models, api


class QueueJob(models.Model):
    _inherit = 'queue.job'

    @api.multi
    def _subscribe_users(self):
        return
