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
from helper_connector import get_environment

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = 'queue.job'

    unwrapped_model = fields.Char(string='unwrapped_model', readonly=True, index=True)
    unwrapped_id = fields.Char(string='unwrapped_id', readonly=True, index=True)
    binding_model = fields.Char(string='binding_model', readonly=True, index=True)
    binding_id = fields.Char(string='binding_id', readonly=True, index=True)

    @api.multi
    def get_job_record_data(self):
        self.ensure_one()
        result = {'unwrapped_model': None,
                  'unwrapped_id': None,
                  'binding_model': None,
                  'binding_id': None}

        try:
            session = ConnectorSession(self.env.cr,
                                       self.env.uid,
                                       context=self.env.context)
            storage = OpenERPJobStorage(session)
            job = storage.load(self.uuid)

            # Get bindings based on the function in func_name
            binding = None
            if job.func_name in [
                        u'openerp.addons.fso_con_getresponse.models.unit_export_delete.export_delete_record',
                        u'openerp.addons.fso_con_getresponse.models.unit_import.import_record']:
                result['binding_model'] = job.args[0]
                binding_backend_id = job.args[1]
                binding_getresponse_id = job.args[2]

                con_env = get_environment(session, result['binding_model'], binding_backend_id)
                binder = con_env.get_connector_unit(Binder)
                binding = binder.to_openerp(binding_getresponse_id, unwrap=False)

            elif job.func_name == u'openerp.addons.fso_con_getresponse.models.unit_export.export_record':
                result['binding_model'] = job.args[0]
                result['binding_id'] = job.args[1]
                binding = session.env[result['binding_model']].browse([result['binding_id']])

            else:
                _logger.debug("%s ist not implemented to extract job data" % job.func_name)
                return result

            # Get job data from binding
            if binding and binding.exists():
                con_env = get_environment(session, binding._name, binding.backend_id.id)
                binder = con_env.get_connector_unit(Binder)

                result['unwrapped_model'] = binder.unwrap_model()
                result['unwrapped_id'] = binder.unwrap_binding(binding.id)
                result['binding_model'] = binding._name
                result['binding_id'] = binding.id
            else:
                _logger.warning("Binding not found for job %s" % repr(self))

        except Exception as e:
            _logger.error("Could not extract job record data %s! %s"
                          "" % (repr(self), repr(e)))
            pass

        return result

    @api.multi
    def update_job_with_source_record_data(self):
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
                    batch_jobs.update_job_with_source_record_data()
                    duration = datetime.now() - batch_start
                    _logger.info("Done _batch_update_job_with_source_record_data for %s jobs in %.3f seconds"
                                 "" % (len(batch_jobs), duration.total_seconds()))
                    # Commit batch run changes to the database
                    batch_env.cr.commit()

    @api.model
    def create(self, vals):
        new_job = super(QueueJob, self).create(vals)
        if new_job:
            new_job.update_job_with_source_record_data()
        return new_job
