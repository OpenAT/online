# -*- coding: utf-8 -*-
from openerp import models, fields


class QueueJob(models.Model):
    _inherit = 'queue.job'

    user_id = fields.Many2one(required=False, ondelete="set null", index=True)
