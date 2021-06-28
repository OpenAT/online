# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime, timedelta

from openerp import models, fields, api, registry, exceptions, _

from openerp.addons.connector.queue.job import STATES, DONE, PENDING, OpenERPJobStorage, JOB_REGISTRY
# from .worker import WORKER_TIMEOUT
from openerp.addons.connector.session import ConnectorSession
# from .worker import watcher
# from ..connector import get_openerp_module, is_module_installed
from openerp.addons.connector.connector import ConnectorEnvironment, Binder

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = 'queue.job'

    unwrapped_model = fields.Char(string='unwrapped_model', readonly=True, index=True)
    unwrapped_id = fields.Char(string='unwrapped_id', readonly=True, index=True)
    binding_model = fields.Char(string='binding_model', readonly=True, index=True)
    binding_id = fields.Char(string='binding_id', readonly=True, index=True)

    @api.multi
    def get_job_record_data(self, raise_exception=False):
        result = {'unwrapped_model': None,
                  'unwrapped_id': None,
                  'binding_model': None,
                  'binding_id': None}
        try:
            self.ensure_one()
            session = ConnectorSession(self.env.cr,
                                       self.env.uid,
                                       context=self.env.context)
            storage = OpenERPJobStorage(session)
            job = storage.load(self.uuid)

            # Get the binding
            binding_model = job.args[0]
            binding_id = job.args[1]
            binding = session.env[binding_model].browse(binding_id)

            if binding.exists():
                result['binding_model'] = binding_model
                result['binding_id'] = binding_id
                # Try to get the unwrapped record also to append it to the job data
                try:
                    env = ConnectorEnvironment(binding.backend_id, session, binding_model)
                    binder = env.get_connector_unit(Binder)
                    unwrapped_model = binder.unwrap_model()
                    unwrapped_id = binder.unwrap_binding(binding_id)
                    if unwrapped_model and unwrapped_id:
                        result['unwrapped_model'] = unwrapped_model
                        result['unwrapped_id'] = unwrapped_id
                except Exception as e:
                    _logger.error("Could not unwrap binding to extend job data %s, %s! %s"
                                  "" % (binding_model, binding_id, repr(e)))
                    pass

        except Exception as e:
            if raise_exception:
                raise e

        return result

    @api.multi
    def _update_job_with_source_record_data(self):
        for job in self:
            job_record_data = job.get_job_record_data()
            try:
                job.write(job_record_data)
            except Exception as e:
                _logger.error('Could not write source_record_data to job %s: %s' % (job.id, repr(e)))
                pass

    @api.multi
    def _batch_update_job_with_source_record_data(self, batch_size=10000):
        assert batch_size > 0, "batch_size must be greater than 0!"
        search_offset = 0
        batch_jobs = True
        while batch_jobs:
            batch_start = datetime.now()
            _logger.info("Start _batch_update_job_with_source_record_data for jobs %s to %s"
                         "" % (search_offset, search_offset+batch_size))
            with api.Environment.manage():
                with registry(self.env.cr.dbname).cursor() as batch_cr:
                    batch_env = api.Environment(batch_cr, self.env.uid, self.env.context)
                    # Search for jobs and update job data
                    batch_jobs = self.with_env(batch_env).search(
                        [('binding_model', '=', False)], limit=batch_size, offset=search_offset)
                    search_offset += batch_size
                    batch_jobs._update_job_with_source_record_data()
                    duration = datetime.now() - batch_start
                    _logger.info("Done _batch_update_job_with_source_record_data for %s jobs in %.3f seconds"
                                 "" % (len(batch_jobs), duration.total_seconds()))
                    # Commit batch run changes to the database
                    batch_env.cr.commit()

    @api.model
    def create(self, vals):
        new_job = super(QueueJob, self).create(vals)
        if new_job:
            new_job._update_job_with_source_record_data()
        return new_job
