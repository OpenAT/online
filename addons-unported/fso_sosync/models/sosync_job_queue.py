# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, SUPERUSER_ID
from openerp.addons.fso_base.tools.validate import is_valid_url
#from openerp.models import MAGIC_COLUMNS
#from openerp.modules.registry import RegistryManager
#from openerp.tools import config

import requests
from requests import Session, Timeout
import datetime
import json

import logging
logger = logging.getLogger(__name__)


# CUSTOM EXCEPTION CLASSES
# class GenericTimeoutError(Exception):
#     def __init__(self):
#         Exception.__init__(self, "Execution stopped because of global timeout and not the request.Session() timeout!"
#                                  "There may be a passphrase in your private key.")


# NEW ODOO MODEL: sosync.job.queue
class SosyncJobQueue(models.Model):
    """
    sosync sync jobs queue

    This is the queue of jobs that needs to be submitted to the sosyncer.
    Submission is done by a simple REST URL call to the sosyncer

    A sync job is basically just a signal that a record had some relevant changes. Directions and final sync
    behaviour is determined by the sync flow!
    """
    _name = 'sosync.job.queue'

    # This is the default sort order of the model! Every search will use this order if order='' is not used!
    _order = 'job_priority DESC, job_date DESC'

    # CONSTANTS
    _systems = [("fso", "FS-Online"), ("fs", "Fundraising Studio")]

    # FIELDS
    job_priority = fields.Integer(string="Job Priority", default=1000,
                                  help="A greater number means a higher priority!")

    # Job Info
    job_date = fields.Datetime(string="Job Date", default=fields.Datetime.now(), readonly=True, index=True)
    job_source_system = fields.Selection(selection=_systems, string="Job Source System", readonly=True)
    job_source_model = fields.Char(string="Job Source Model", readonly=True)
    job_source_record_id = fields.Integer(string="Job Source Record ID", readonly=True)
    job_source_target_record_id = fields.Integer(string="Job Source Target Record ID", readonly=True,
                                                 help="Only filled if already available in the job source system at "
                                                      "job creation time")  # NEW

    # Additional info for merge and delete sync jobs
    # HINT: It would be best if this information could be retrieved from the job source system by the sync flow
    #       but for now this is the quicker next-best-alternative
    job_source_type = fields.Selection(string="Job Source Type", selection=[("delete", "Delete"),
                                                                            ("merge_into", "Merge Into")],
                                       help="Job type indicator for special sync jobs. "
                                            "If empty it is processed as a default sync job = 'create' or 'update'",
                                       readonly=True, default=False)
    job_source_merge_into_record_id = fields.Integer(string="Job Source Merge-Into Record ID", readonly=True)
    job_source_target_merge_into_record_id = fields.Integer(string="Job Source Merge-Into Target Record ID",
                                                            readonly=True)  # NEW

    job_source_sosync_write_date = fields.Char(string="Job Source sosync_write_date", readonly=True)
    job_source_fields = fields.Text(string="Job Source Fields", readonly=True)

    # Submission Info
    submission_state = fields.Selection(selection=[("new", "New"),
                                                   ("submitted", "Submitted"),
                                                   ("submission_error", "Submission Error")],
                                        string="State", default="new", readonly=True,
                                        index=True)
    submission = fields.Datetime(string="Submission", readonly=True)
    submission_url = fields.Char(sting="Submission URL", readonly=True)
    submission_response_code = fields.Char(string="Response Code", help="HTTP Response Code", readonly=True)
    submission_response_body = fields.Text(string="Response Body", readonly=True)

    submission_error = fields.Selection(selection=[("timeout", "Request timed out"),
                                                   ("not_available", "Service not available"),
                                                   ("error", "Request error")],
                                        string="Submission Error", readonly=True)

    def init(self, cr, context=None):
        # Remove scheduled cron job to make sure it will be recreated with values from xml file
        model_data_obj = self.pool.get('ir.model.data')
        scheduler_a = model_data_obj.xmlid_to_object(cr, SUPERUSER_ID, 'fso_sosync.ir_cron_scheduled_job_queue_cleanup_1')
        if scheduler_a:
            logger.info("Unlink fso_sosync.ir_cron_scheduled_job_queue_cleanup_1 on install/update for recreation!")
            scheduler_a.unlink()

        # TODO: Remove this code after sosync.job model was removed on all instances
        # Remove scheduled cron job to make sure it will be recreated with values from xml file
        model_data_obj = self.pool.get('ir.model.data')
        scheduler_b = model_data_obj.xmlid_to_object(cr, SUPERUSER_ID,
                                             'fso_sosync.ir_cron_scheduled_cleanup_sosync_job_model_and_table')
        if scheduler_b:
            logger.info("Unlink ir_cron_scheduled_cleanup_sosync_job_model_and_table on install/update for recreation!")
            scheduler_b.unlink()

    # METHODS
    @api.multi
    def submit_sync_job(self, instance="", url="", http_header={},
                        crt_pem="", prvkey_pem="", user="", pwd="", timeout=60*1.5):

        # Get the 'Instance ID' (e.g.: care) from the main instance company for the default service sosync url
        instance = instance or self.env['res.company'].sudo().search([("instance_company", "=", True)],
                                                                     limit=1).instance_id
        assert instance, "'Instance ID' for the main instance company is missing!"

        # Sosync service url (in internal network)
        url_overwrite = self.env['res.company'].sudo().search([("instance_company", "=", True)], limit=1)
        if url_overwrite:
            url_overwrite = url_overwrite.sosync_job_submission_url
        url = url or url_overwrite or "http://sosync."+instance+".datadialog.net/job/create"
        is_valid_url(url=url, dns_check=False)

        # Create a Session Object (just like a regular UA e.g. Firefox or Chrome)
        session = Session()
        session.verify = True
        if crt_pem and prvkey_pem:
            session.cert = (crt_pem, prvkey_pem)
        if user and pwd:
            session.auth(user, pwd)

        # Check if sync jobs to submit are already submitted
        submitted_jobs = self.filtered(lambda r: r.submission_state == 'submitted')
        if submitted_jobs:
            logger.warning("bulk_submit_sync_job() jobs found to submit that are already in state 'submitted' "
                           "(IDs: %s)!" % submitted_jobs.ids)

        # Submit every sync Job as a POST call to the sosyncer v2
        for record in self:
            logger.debug("Submitting sosync sync-job %s from queue to %s!" % (record.id, url))
            http_header = http_header or {
                'content-type': 'application/json; charset=utf-8',
            }
            data = {'job_date': record.job_date,
                    'job_source_system': record.job_source_system,
                    'job_source_model': record.job_source_model,
                    'job_source_record_id': record.job_source_record_id,
                    'job_source_target_record_id': record.job_source_target_record_id,
                    'job_source_sosync_write_date': record.job_source_sosync_write_date,
                    'job_source_fields': record.job_source_fields,
                    'job_source_type': record.job_source_type,
                    'job_source_merge_into_record_id': record.job_source_merge_into_record_id,
                    'job_source_target_merge_into_record_id': record.job_source_target_merge_into_record_id,
                    }
            # Convert python dictionary with unicode values to ascii json object with escaped UTF-8 chars
            data_json_ascii = json.dumps(data, ensure_ascii=True)
            submission = fields.Datetime.now()
            try:
                response = requests.post(url, headers=http_header, timeout=timeout, data=data_json_ascii)
            # Timeout Exception
            except Timeout as e:
                logger.error("Submitting sosync sync-job %s request Timeout exception!" % record.id)
                record.sudo().write({'submission_state': 'submission_error',
                                     'submission': submission,
                                     'submission_url': url,
                                     'submission_error': 'timeout',
                                     'submission_response_code': '',
                                     'submission_response_body': "Request Timeout:\n%s" % e})
                continue

            # Generic Exception
            except Exception as e:
                logger.error("Submitting sosync sync-job %s exception: %s" % (record.id, repr(e)))
                record.sudo().write({'submission_state': 'submission_error',
                                     'submission_url': url,
                                     'submission': submission,
                                     'submission_error': 'error',
                                     'submission_response_code': '',
                                     'submission_response_body': "Request Exception:\n%s" % e})
                continue

            # HTTP Error Code returned
            if response.status_code != requests.codes.ok:
                logger.error("Submitting sosync sync-job %s error: %s" % (record.id, response.content))
                record.sudo().write({'submission_state': 'submission_error',
                                     'submission_url': url,
                                     'submission': submission,
                                     'submission_error': 'error',
                                     'submission_response_code': response.status_code,
                                     'submission_response_body': response.content})
                continue

            # Submission was successful
            record.sudo().write({'submission_state': 'submitted',
                                 'submission_url': url,
                                 'submission': submission,
                                 'submission_error': '',
                                 'submission_response_code': response.status_code,
                                 'submission_response_body': response.content})

    @api.multi
    def bulk_submit_sync_job(self, instance="", url="", http_header={},
                             crt_pem="", prvkey_pem="", user="", pwd="", timeout=60*5):

        # Get the 'Instance ID' (e.g.: care) from the main instance company for the default service sosync url
        instance = instance or self.env['res.company'].sudo().search([("instance_company", "=", True)],
                                                                     limit=1).instance_id
        assert instance, "'Instance ID' for the main instance company is missing!"

        # Sync job bulk submission url (in internal network)
        url_overwrite = self.env['res.company'].sudo().search([("instance_company", "=", True)], limit=1)
        if url_overwrite:
            url_overwrite = url_overwrite.sosync_job_submission_url
        url = url or url_overwrite or "http://sosync."+instance+".datadialog.net/job/bulk-create"
        is_valid_url(url=url, dns_check=False)

        # Create a Session Object (just like a regular UA e.g. Firefox or Chrome)
        session = Session()
        session.verify = True
        if crt_pem and prvkey_pem:
            session.cert = (crt_pem, prvkey_pem)
        if user and pwd:
            session.auth(user, pwd)

        # Check if sync jobs to submit are already submitted
        submitted_jobs = self.filtered(lambda r: r.submission_state == 'submitted')
        if submitted_jobs:
            logger.warning("bulk_submit_sync_job() jobs found to submit that are already in state 'submitted' "
                           "(IDs: %s)!" % submitted_jobs.ids)

        # PREPARE DATA
        # ---
        all_jobs = []
        logger.info("Prepare %s sync jobs for submission" % len(self))
        for record in self:
            logger.debug("Preparing sosync sync-job %s from queue!" % record.id)
            job_data = {'job_date': record.job_date,
                        'job_source_system': record.job_source_system,
                        'job_source_model': record.job_source_model,
                        'job_source_record_id': record.job_source_record_id,
                        'job_source_target_record_id': record.job_source_target_record_id,
                        'job_source_sosync_write_date': record.job_source_sosync_write_date,
                        'job_source_fields': record.job_source_fields,
                        'job_source_type': record.job_source_type,
                        'job_source_merge_into_record_id': record.job_source_merge_into_record_id,
                        'job_source_target_merge_into_record_id': record.job_source_target_merge_into_record_id,
                        }
            # Append sync job to the 'all_jobs' list
            all_jobs.append(job_data)

        # SUBMIT THE SYNC JOBS AS JSON STRING
        # ---
        logger.info("Bulk submit %s sync jobs to %s" % (len(self), url))
        submission = fields.Datetime.now()
        try:
            response = requests.post(url,
                                     headers=http_header or {'content-type': 'application/json; charset=utf-8'},
                                     timeout=timeout,
                                     data=json.dumps(all_jobs, ensure_ascii=True))

        # Timeout Exception
        except Timeout as e:
            logger.error("Submitting %s sync-jobs failed! Timeout exception!" % len(self))
            self.sudo().write({'submission_state': 'submission_error',
                               'submission': submission,
                               'submission_url': url,
                               'submission_error': 'timeout',
                               'submission_response_code': '',
                               'submission_response_body': "Request Timeout:\n%s" % e})
            return False

        # Generic Exception
        except Exception as e:
            logger.error("Submitting %s sync-jobs failed! Exception: %s" % (len(self), repr(e)))
            self.sudo().write({'submission_state': 'submission_error',
                               'submission_url': url,
                               'submission': submission,
                               'submission_error': 'error',
                               'submission_response_code': '',
                               'submission_response_body': "Request Exception:\n%s" % e})
            return False

        # HTTP Error Code returned
        if response.status_code != requests.codes.ok:
            logger.error("Submitting %s sync-jobs failed! Error: %s" % (len(self), response.content or ''))
            self.sudo().write({'submission_state': 'submission_error',
                               'submission_url': url,
                               'submission': submission,
                               'submission_error': 'error',
                               'submission_response_code': response.status_code,
                               'submission_response_body': response.content})
            return False

        # Submission was successful
        self.sudo().write({'submission_state': 'submitted',
                           'submission_url': url,
                           'submission': submission,
                           'submission_error': '',
                           'submission_response_code': response.status_code,
                           'submission_response_body': response.content})
        return True

    # --------------------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED JOB QUEUE SUBMISSION
    # --------------------------------------------------
    @api.model
    def scheduled_job_queue_submission(self, limit=0):

        # Limit the number of submissions per scheduled run to the interval length in seconds
        # HINT: This suggests that a submission should time-out after one second
        scheduled_action = self.env.ref('fso_sosync.ir_cron_scheduled_job_queue_submission')
        interval_to_seconds = {
            "weeks": 7 * 24 * 60 * 60,
            "days": 24 * 60 * 60,
            "hours": 60 * 60,
            "minutes": 60,
            "seconds": 1
        }
        # Lowest interval is 60 seconds for cron jobs
        runtime_in_sec = 60
        if scheduled_action and scheduled_action.interval_type in interval_to_seconds:
            runtime_in_sec = int(scheduled_action.interval_number * interval_to_seconds[scheduled_action.interval_type])
            # Raise job limit to 40 jobs per second (1000/40 = 25ms for one job to submit)
            limit = runtime_in_sec * 40

        # Make sure there is at least one job loaded for submission
        limit = 1 if limit <= 0 else limit

        max_runtime_in_sec = runtime_in_sec - 1

        logger.info("Scheduled sync-job-queue submission! "
                    "max-runtime in seconds: %s, max-jobs to submit: %s" % (max_runtime_in_sec, limit))

        # Search for new sync jobs to submit
        # HINT: Search for jobs in queue with errors first to block further submission until this jobs are submitted
        jobs_in_queue = self.search([('submission_state', '=', 'submission_error')], limit=limit)
        if not jobs_in_queue:
            jobs_in_queue = self.search([('submission_state', '=', 'new')], limit=limit)

        # Submit jobs to sosync service
        runtime_start = datetime.datetime.now()
        runtime_end = runtime_start + datetime.timedelta(0, max_runtime_in_sec)

        # BULK SUBMIT SYNC JOBS IN QUEUE
        # ---
        try:
            jobs_in_queue.bulk_submit_sync_job()
        except Exception as e:
            logger.info("Bulk submission of sync jobs failed! %s" % repr(e))
            return False

        logger.info("Processed %s Sync Jobs" % len(jobs_in_queue))
        return True

    @api.model
    def scheduled_delete_old_jobs(self):
        self.delete_old_jobs()

    # -------------------
    # METHODS FOR CLEANUP
    # -------------------
    @api.model
    def delete_old_jobs(self, limit=100000):
        delete_before = datetime.datetime.now() - datetime.timedelta(days=30)
        delete_before = delete_before.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        domain = [('job_date', '<=', delete_before),
                  ('submission_state', '=', 'submitted')]
        jobs_to_delete = self.search(domain, limit=limit)
        if jobs_to_delete:
            logger.warning("Found %s jobs in job queue for cleanup." % len(jobs_to_delete))
            jobs_to_delete.unlink()

    # TODO: Remove this method and related cron job after all instances are cleared from sosync.job
    @api.model
    def cleanup_sosync_job_model_and_table(self):
        logger.info("START cleanup_sosync_job_model_and_table()")

        # sosync_job_model = False
        # if hasattr(self, 'pool') and 'sosync.job' in self.pool.models:
        #     sosync_job_model = self.env['ir.model'].search([('model', '=', 'sosync.job')])

        sosync_job_model = self.env['ir.model'].search([('model', '=', 'sosync.job')])

        if sosync_job_model:
            logger.info("sosync.job model (ID %s) found" % sosync_job_model.id)

            # Convert this model to a 'custom model' (state='manual') first to allow the unlink
            # HINT: Check ir_model.py>unlink()@175 to see why this is needed
            logger.info("Checking sosync.job model state ('%s')" % sosync_job_model.state)
            if sosync_job_model.state != 'manual':
                logger.info("Setting sosync.job model state (%s) to 'manual'" % sosync_job_model.state)
                sosync_job_model.state = 'manual'

            # Remove any leftover model constraints
            sosync_job_model_contraints = self.env['ir.model.constraint'].search([('model', '=', 'sosync.job')])
            if sosync_job_model_contraints:
                try:
                    logger.info("Removing %s ir.model.constraint for sosync.job model"
                                "" % len(sosync_job_model_contraints))
                    sosync_job_model_contraints.unlink()
                except Exception as e:
                    logger.error("Unlink of model constraint failed: %s" % repr(e))
                    raise

            # ATTENTION: Because the model was already removed it will not be in self.pool.models on init or update of
            #            the fso_sosync addon. Without -u or -i of fso_sosync it will be there because it still exits
            #            in the database in ir.model. A bit like a chicken and egg problem ... Therefore it can not be
            #            unlinked on init or update of fso_sosync or any addon that depends on it. Because of this
            #            i added it to delete_old_jobs() as an UGLY workaround.
            # ATTENTION: It needs a restart after cleanup_sosync_job_model_and_table did run the first time
            #            The reason is unknown to me. But therefore i added it to actions_on_update_install.xml
            if hasattr(self, 'pool'):
                logger.info('Check if sosync.job is in self.pool.models')
                if 'sosync.job' in self.pool.models:
                    try:
                        logger.info("Unlink ir.model sosync.job")
                        sosync_job_model.unlink()
                    except Exception as e:
                        logger.error("Could not unlink ir.model sosync.job: %s" % repr(e))
                        raise
