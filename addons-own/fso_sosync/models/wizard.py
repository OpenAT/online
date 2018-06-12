# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

import datetime
import logging
logger = logging.getLogger(__name__)


class DeleteSyncJobWizard(models.TransientModel):
    _name = 'sosync.job.wizard'

    delete_jobs_before = fields.Datetime(string='Delete Sync Jobs with last write before')
    delete_jobs_state = fields.Selection(selection=[("new", "New"),
                                                    ("inprogress", "In Progress"),
                                                    ("child", "ChildJob Processing"),
                                                    ("done", "Done"),
                                                    ("error", "Error"),
                                                    ("skipped", "Skipped")],
                                         string="In State", default='done')

    sync_job_ids = fields.Many2many('sosync.job.queue', string="Sync Jobs to Delete",
                                    readonly=True, compute="_compute_sync_job_ids")

    @api.onchange('delete_jobs_before', 'delete_jobs_state')
    def _compute_sync_job_ids(self):
        for r in self:

            if r.delete_jobs_before:
                djb = datetime.datetime.strptime(r.delete_jobs_before, DEFAULT_SERVER_DATETIME_FORMAT)
                if djb >= (datetime.datetime.now() - datetime.timedelta(days=60)):
                    raise ValidationError(_("You can only delete sync jobs without activity for more than "
                                            "60 days!\nPlease change the 'Delete Sync Jobs before' date."))

                domain = [('write_date', '<=', r.delete_jobs_before)]
                if r.delete_jobs_state:
                    domain += [('job_state', '=', r.delete_jobs_state)]

                logger.info("Wizard domain: %s" % domain)
                jobs_to_delete = r.env['sosync.job'].search(domain)

                if jobs_to_delete:
                    r.sync_job_ids = jobs_to_delete
            else:
                r.sync_job_ids = False

    @api.multi
    def delete_sync_jobs(self):
        assert self.ensure_one(), "Only one wizard at a time!"

        if self.sync_job_ids:
            logger.warning("The wizard will delete %s sync jobs!" % len(self.sync_job_ids))
            self.sync_job_ids.unlink()

        return {}


class DeleteSyncJobQueueWizard(models.TransientModel):
    _name = 'sosync.job.queue.wizard'

    delete_jobs_before = fields.Datetime(string='Delete Queued Sync Jobs before')
    delete_jobs_state = fields.Selection(selection=[("new", "New"),
                                                    ("submitted", "Submitted"),
                                                    ("submission_error", "Submission Error")],
                                         string="In State", default='submitted')

    sync_job_ids = fields.Many2many('sosync.job.queue', string="Sync Jobs to Delete",
                                    readonly=True, compute="_compute_sync_job_ids")

    @api.onchange('delete_jobs_before', 'delete_jobs_state')
    def _compute_sync_job_ids(self):
        for r in self:

            if r.delete_jobs_before:
                djb = datetime.datetime.strptime(r.delete_jobs_before, DEFAULT_SERVER_DATETIME_FORMAT)
                if djb >= (datetime.datetime.now() - datetime.timedelta(days=60)):
                    raise ValidationError(_("You can only delete queued sync jobs that are at least older than "
                                            "60 days!\nPlease change the 'Delete Sync Jobs before' date."))

                domain = [('job_date', '<=', r.delete_jobs_before)]
                if r.delete_jobs_state:
                    domain += [('submission_state', '=', r.delete_jobs_state)]

                logger.info("Wizard domain: %s" % domain)
                jobs_to_delete = r.env['sosync.job.queue'].search(domain)

                if jobs_to_delete:
                    r.sync_job_ids = jobs_to_delete
            else:
                r.sync_job_ids = False

    @api.multi
    def delete_queued_sync_jobs(self):
        assert self.ensure_one(), "Only one wizard at a time!"

        if self.sync_job_ids:
            logger.warning("The wizard will delete %s queued sync jobs!" % len(self.sync_job_ids))
            self.sync_job_ids.unlink()

        return {}
