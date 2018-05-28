# -*- coding: utf-'8' "-*-"
import logging
from openerp import api, models, fields, osv
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.validate import is_valid_url
from openerp.exceptions import ValidationError

import requests
from requests import Request, Session
from requests import Timeout
from dateutil import parser
import datetime
import json

logger = logging.getLogger(__name__)


# CUSTOM EXCEPTION CLASSES
class GenericTimeoutError(Exception):
    def __init__(self):
        Exception.__init__(self, "Execution stopped because of global timeout and not the request.Session() timeout!"
                                 "There may be a passphrase in your private key.")


# HELPER FUNCTIONS
def _duration_in_ms(start_datetime, end_datetime):
    try:
        duration = parser.parse(end_datetime) - parser.parse(start_datetime)
        return int(duration.total_seconds() * 1000)
    except:
        pass
    return None


class ResCompanySosyncSettings(models.Model):
    _inherit = "res.company"

    # Job submission url overwrite for debugging purposes
    sosync_job_submission_url = fields.Char(string="sosync job sumission URL",
                                            help="Overwrite for the sosync job submission URL. "
                                                 "Keep empty for default URL!")


# NEW ODOO MODEL: sosync.job
class SosyncJob(models.Model):
    """
    sosync sync jobs

    A sync job is basically just a signal that a record had some relevant changes. Directions and final sync
    behaviour is determined by the sync flow!
    """
    _name = 'sosync.job'

    # CONSTANTS
    _systems = [("fso", "FS-Online"), ("fs", "Fundraising Studio")]

    # Default order
    _order = 'job_start DESC, write_date DESC, job_date DESC, job_fetched DESC'

    # Create combined index for faster tree view
    def _auto_init(self, cr, context=None):
        res = super(SosyncJob, self)._auto_init(cr, context=context)
        cr.execute('SELECT indexname FROM pg_indexes '
                   'WHERE indexname = \'sosync_job_job_start_write_date_job_date_job_fetched_index\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX sosync_job_job_start_write_date_job_date_job_fetched_index '
                       'ON sosync_job (job_start DESC, write_date DESC, job_date DESC, job_fetched DESC)')
        return res

    # ======
    # FIELDS
    # ======
    # Add an index to create_date
    create_date = fields.Datetime(index=True)
    # Add an index to write_date
    write_date = fields.Datetime(index=True)

    # SYNCJOB
    job_id = fields.Integer(string="Job ID", readonly=True,
                            index=True)
    job_date = fields.Datetime(string="Job Date", default=fields.Datetime.now(), readonly=True,
                               index=True)

    # SYNCJOB SOURCE
    job_source_system = fields.Selection(selection=_systems, string="Job Source System", readonly=True,
                                         index=True)
    job_source_model = fields.Char(string="Job Source Model", readonly=True,
                                   index=True)
    job_source_record_id = fields.Integer(string="Job Source Record ID", readonly=True,
                                          index=True)
    job_source_target_record_id = fields.Integer(string="Job Source Target Record ID", readonly=True,
                                                 help="Only filled if the target system id is already available in the "
                                                      "job source system at job creation time!",
                                                 index=True)   # NEW
    job_source_sosync_write_date = fields.Char(string="Job Source sosync_write_date", readonly=True,
                                               index=True)
    job_source_fields = fields.Text(string="Job Source Fields", readonly=True)

    # Additional info for merge and delete sync jobs
    # HINT: It would be best if this information could be retrieved from the job source system by the sync flow
    #       but for now this is the quicker next-best-alternative
    job_source_type = fields.Selection(string="Job Source Type", selection=[("delete", "Delete"),
                                                                            ("merge_into", "Merge Into"),
                                                                            ("temp", "Temporary Flow")
                                                                            ],
                                       help="Job type indicator for special sync jobs. "
                                            "If empty it is processed as a default sync job = 'create' or 'update'",
                                       readonly=True, default=False,
                                       index=True)
    job_source_type_info = fields.Char(string='Indicator for temporary sync flows', readonly=True, index=True,
                                       help="Indicator for repair sync flows (to group by later on) "
                                            "e.g.: 'donation_deduction_disabled_repair' This should NOT be used for"
                                            "long descriptions!")

    job_source_merge_into_record_id = fields.Integer(string="Job Source Merge-Into Record ID", readonly=True)
    job_source_target_merge_into_record_id = fields.Integer(string="Job Source Merge-Into Target Record ID",
                                                            readonly=True)  # NEW

    # SYNCJOB INFO
    job_fetched = fields.Datetime(string="Job Fetched Date", readonly=True)
    job_start = fields.Char(string="Job Start", readonly=True,
                            index=True)
    job_end = fields.Char(string="Job End", readonly=True,
                          index=True)
    job_duration = fields.Integer(string="Job Duration (ms)", compute='_job_duration', readonly=True)
    job_run_count = fields.Integer(string="Job Run Count", readonly=True,
                                   help="Restarts triggered by changed source data in between job processing")
    # HINT: If a sync job is related to a flow listed in the instance pillar option "sosync_skipped_flows"
    #       the job and any related parent-job will get the state "skipped" from the sosyncer service
    job_state = fields.Selection(selection=[("new", "New"),
                                            ("inprogress", "In Progress"),
                                            ("child", "ChildJob Processing"),
                                            ("done", "Done"),
                                            ("error", "Error"),
                                            ("skipped", "Skipped")],
                                 string="State", default="new", readonly=True,
                                 index=True)
    job_error_code = fields.Selection(selection=[("timeout", "Job timed out"),
                                                 ("run_counter", "Run count exceeded"),
                                                 ("child_job", "Child job error"),
                                                 ("sync_source", "Could not determine sync direction"),
                                                 ("transformation", "Model transformation error"),
                                                 ("cleanup", "Job finalization error"),
                                                 ("unknown", "Unexpected error")],
                                      string="Error Code", readonly=True,
                                      index=True)
    job_error_text = fields.Text(string="Error", readonly=True)
    job_log = fields.Text(string="Job Log", readonly=True)

    # PARENT JOB
    parent_job_id = fields.Integer(string="Parent Job ID", help="Parent Job ID (from field job_id)", readonly=True,
                                   index=True)

    # ODOO ONLY (to show a hierarchy view later on in the odoo gui)
    #           (TODO: must be computed fields based on job id and parent_job_id)
    parent_job_odoo = fields.Many2one(comodel_name="sosync.job", string="Parent Job", readonly=True)
    child_jobs_odoo = fields.One2many(comodel_name="sosync.job", inverse_name="parent_job_odoo", string="Child Jobs",
                                      readonly=True)

    # CHILD JOBS PROCESSING TIME
    child_job_start = fields.Char(string="Child Processing Start", readonly=True)
    child_job_end = fields.Char(string="Child Processing End", readonly=True)
    child_job_duration = fields.Integer(string="Child Processing Duration", compute="_child_duration", readonly=True)

    # SYNCHRONIZATION SOURCE
    sync_source_system = fields.Selection(selection=_systems, string="Source System", readonly=True,
                                          index=True)
    sync_source_model = fields.Char(string="Source Model", readonly=True,
                                    index=True)
    sync_source_record_id = fields.Integer(string="Source Record ID", readonly=True)
    sync_source_merge_into_record_id = fields.Integer(string="Source Merge-Into Record ID", readonly=True)  # NEW

    # SYNCHRONIZATION TARGET
    sync_target_system = fields.Selection(selection=_systems, string="Target System", readonly=True,
                                          index=True)
    sync_target_model = fields.Char(string="Target Model", readonly=True,
                                    index=True)
    sync_target_record_id = fields.Integer(string="Target Record ID", readonly=True)
    sync_target_merge_into_record_id = fields.Integer(string="Target Merge-Into Record ID", readonly=True)  # NEW

    # SYNCHRONIZATION INFO
    sync_source_data = fields.Text(string="Sync Source Data", readonly=True)

    sync_target_data_before = fields.Text(string="Sync Target Data before", readonly=True) # Not used in odoo
    sync_target_request = fields.Text(string="Sync Target Request(s)", readonly=True)
    sync_target_answer = fields.Text(string="Sync Target Answer(s)", readonly=True)
    sync_target_data_after = fields.Text(string="Sync Target Data after", readonly=True) # Not used in odoo

    sync_start = fields.Char(string="Sync Start", readonly=True)
    sync_end = fields.Char(string="Sync End", readonly=True)
    sync_duration = fields.Integer(string="Sync Duration (ms)", compute="_target_request_duration", readonly=True)

    # COMPUTED FIELDS METHODS
    @api.depends('job_start', 'job_end')
    def _job_duration(self):
        for rec in self:
            if rec.job_start and rec.job_end:
                rec.job_duration = _duration_in_ms(rec.job_start, rec.job_end)

    @api.depends('sync_start', 'sync_end')
    def _target_request_duration(self):
        for rec in self:
            if rec.sync_start and rec.sync_end:
                rec.sync_duration = _duration_in_ms(rec.sync_start, rec.sync_end)

    @api.depends('child_job_start', 'child_job_end')
    def _child_duration(self):
        for rec in self:
            if rec.child_job_start and rec.child_job_end:
                rec.child_job_duration = _duration_in_ms(rec.child_job_start, rec.child_job_end)
                
    # ATTENTION: Since this is used as a server action do not use any additional interface arguments :(
    @api.multi
    def copy_sync_job_to_queue(self, job_limit=100000):
        if not self:
            return

        jobs_count = len(self)
        if jobs_count > job_limit:
            raise ValidationError(_("You are trying to copy %s sync jobs to the submission queue but only up "
                                    "to %s are allowed!") % (jobs_count, job_limit))
        logger.info("Copy %s sync jobs to submission queue!" % len(self))

        job_queue = self.env['sosync.job.queue']
        now = fields.Datetime.now()
        for rec in self:
            data = {'job_date': now,
                    'job_source_system': rec.job_source_system,
                    'job_source_model': rec.job_source_model,
                    'job_source_record_id': rec.job_source_record_id,
                    'job_source_target_record_id': rec.job_source_target_record_id,
                    #
                    'job_source_type': rec.job_source_type,
                    'job_source_merge_into_record_id': rec.job_source_merge_into_record_id,
                    'job_source_target_merge_into_record_id': rec.job_source_target_merge_into_record_id,
                    #
                    'job_source_sosync_write_date': rec.job_source_sosync_write_date,
                    'job_source_fields': rec.job_source_fields,
                    }
            job_queue.sudo().create(data)


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

    # CONSTANTS
    _systems = [("fso", "FS-Online"), ("fs", "Fundraising Studio")]

    # FIELDS
    # Job Info
    job_date = fields.Datetime(string="Job Date", default=fields.Datetime.now(), readonly=True)
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

    # METHODS
    @api.multi
    def submit_sync_job(self, instance="", url="", http_header={},
                        crt_pem="", prvkey_pem="", user="", pwd="", timeout=4):

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
            # Raise job limit to 200 jobs per second
            # Now the limit would be one job per second which is way to low therefore we multiply it by 200
            # so we estimate that one job could be received by the sosyncer every 50 ms
            limit = runtime_in_sec * 200

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
        processed_jobs_counter = 0
        for job in jobs_in_queue:
            if datetime.datetime.now() >= runtime_end:
                break
            job.submit_sync_job()
            processed_jobs_counter += 1

        # Log processing info
        logger.info("Processed %s Sync Jobs" % processed_jobs_counter)


# NEW ABSTRACT MODEL: base.sosync
# Use this for all models where yout want to enable sosync sync job creation
class BaseSosync(models.AbstractModel):
    _name = "base.sosync"

    # NEW COMMON FIELDS
    sosync_fs_id = fields.Integer(string="Fundraising Studio ID", readonly=True, index=True)
    sosync_write_date = fields.Char(string="Sosync Write Date", readonly=True, index=True,
                                    help="Last change of one or more sosync-tracked-fields.")
    # HINT: Is a char field to show exact ms
    sosync_sync_date = fields.Char(string="Last sosync sync", readonly=True,
                                   help="Exact datetime of source-data-readout for the sync job!")

    # Extend the fields.get of openerp.Basemodel to include the sosync attribute for the java script
    # field manager for website forms to make it possible highlight sosynced watched fields in the backend
    def fields_get(self, cr, user, allfields=None, context=None, write_access=True, attributes=None):
        res = super(BaseSosync, self).fields_get(cr, user, allfields=allfields, context=context,
                                                      write_access=write_access, attributes=attributes)
        for fname, field in self._fields.iteritems():
            if hasattr(field, "_attrs"):
                sosync = field._attrs.get("sosync")
                if sosync and fname in res:
                    res[fname].update({"sosync": sosync})

        return res

    @api.model
    def _sosync_write_date_now(self):
        return datetime.datetime.utcnow().isoformat() + "Z"

    @api.model
    def _get_sosync_tracked_fields(self, updated_fields=list()):
        sosync_tracked_fields = list()

        for name, field in self._fields.items():
            if getattr(field, 'sosync', False) or name in updated_fields:
                sosync_tracked_fields.append(name)

        return sosync_tracked_fields

    @api.model
    def _sosync_watched_fields(self, values={}):
        tracked_fields = self._get_sosync_tracked_fields()
        watched_fields = {key: values[key] for key in values if key in tracked_fields}
        return watched_fields

    @api.multi
    def create_sync_job(self, job_date=False, sosync_write_date=False, job_source_fields=False, job_source_type=False,
                        job_source_merge_into_record_id=False, job_source_target_merge_into_record_id=False):
        # HINT: sosync_write_date may be emtpy for initial sync of records sosync v2 uses write date as a fallback
        # HINT: job_source_fields may be empty by sync job creation in gui
        job_date = job_date or fields.Datetime.now()
        job_queue = self.env["sosync.job.queue"].sudo()
        model = self._name
        for record in self:
            sosync_write_date = sosync_write_date or record.sosync_write_date
            job = job_queue.create({"job_date": job_date,
                                    "job_source_system": "fso",
                                    "job_source_model": model,
                                    "job_source_record_id": record.id,
                                    "job_source_target_record_id": record.sosync_fs_id,
                                    "job_source_sosync_write_date": sosync_write_date,
                                    "job_source_fields": job_source_fields,
                                    "job_source_type": job_source_type,
                                    "job_source_merge_into_record_id": job_source_merge_into_record_id,
                                    "job_source_target_merge_into_record_id": job_source_target_merge_into_record_id,
                                    })
            logger.debug("Sosync SyncJob %s created for %s with id %s in queue!" % (job.id, model, record.id))
        return True

    @api.model
    def create(self, values, **kwargs):
        # CREATE SYNC JOBS
        # ----------------
        values = values or dict()

        # Get create_sync_job from context or set it to True
        # HINT: create_sync_job is a switch in the context dict to suppress sync job generation
        #       This is mandatory for all updates from the sosyncer service to avoid endless sync job generation!
        if not self.env.context:
            create_sync_job = True
        else:
            create_sync_job = self.env.context.get("create_sync_job", True)

        # Make sure sync jobs creation is enabled in the context again
        # ATTENTION: "create_sync_job" is set to "True" again in the context before any other method is called!
        #            Therefore possible updates in other models can still create sync jobs which is the
        #            intended and correct behaviour!
        if not create_sync_job:
            self = self.with_context(create_sync_job=True)

        # Find all watched Fields
        watched_fields = self._sosync_watched_fields(values)
        try:
            watched_fields_repr = {key: str(values[key]) for key in values if key in watched_fields}
            watched_fields_json = json.dumps(watched_fields_repr, ensure_ascii=False)
        except:
            watched_fields_json = watched_fields
            pass

        # Set the sosync_write_date
        sosync_write_date = self._sosync_write_date_now()

        # Create the record
        if create_sync_job and watched_fields:
            values["sosync_write_date"] = sosync_write_date
        rec = super(BaseSosync, self).create(values, **kwargs)

        # Create the sync job
        if create_sync_job and watched_fields and rec:
            rec.create_sync_job(sosync_write_date=sosync_write_date, job_source_fields=watched_fields_json)

        return rec

    @api.multi
    def write(self, values, **kwargs):
        # CREATE SYNC JOBS
        # ----------------
        values = values or dict()

        # Get create_sync_job from context or set it to True
        # HINT: create_sync_job is a switch in the context dict to suppress sync job generation
        #       This is mandatory for all updates from the sosyncer service to avoid endless sync job generation!
        # ATTENTION: "create_sync_job" is set to "True" in the context before any other method is called!
        #            Therefore possible updates in other models can still create sync jobs which is the intended
        #            and correct behaviour!
        if not self.env.context:
            create_sync_job = True
        else:
            create_sync_job = self.env.context.get("create_sync_job", True)

        # Make sure sync jobs creation is enabled in the context again
        # ATTENTION: "create_sync_job" is set to "True" again in the context before any other method is called!
        #            Therefore possible updates in other models can still create sync jobs which is the
        #            intended and correct behaviour!
        if not create_sync_job:
            self = self.with_context(create_sync_job=True)

        # Find all watched Fields
        watched_fields = self._sosync_watched_fields(values)
        try:
            watched_fields_repr = {key: str(values[key]) for key in values if key in watched_fields}
            watched_fields_json = json.dumps(watched_fields_repr, ensure_ascii=False)
        except:
            watched_fields_json = watched_fields
            pass

        # Create sync job(s) and set the sosync_write_date
        # HINT: This is done "before" the actual write because if something goes wrong when trying to create the sync
        #       job the write to the record should not be done (rollback) because sync job creation is crucial!
        if create_sync_job and watched_fields:
            sosync_write_date = self._sosync_write_date_now()
            for record in self:
                record.create_sync_job(sosync_write_date=sosync_write_date, job_source_fields=watched_fields_json)
            values["sosync_write_date"] = sosync_write_date

        # Continue with write method
        return super(BaseSosync, self).write(values, **kwargs)

    @api.multi
    def unlink(self):
        # Get create_sync_job from context or set it to True
        # HINT: create_sync_job is a switch in the context dict to suppress sync job generation
        #       This is mandatory for all updates from the sosyncer service to avoid endless sync job generation!
        # ATTENTION: "create_sync_job" is set to "True" in the context before any other method is called!
        #            Therefore possible updates in other models can still create sync jobs which is the intended
        #            and correct behaviour!
        if not self.env.context:
            create_sync_job = True
        else:
            create_sync_job = self.env.context.get("create_sync_job", True)

        # Make sure sync jobs creation is enabled in the context again
        # ATTENTION: "create_sync_job" is set to "True" again in the context before any other method is called!
        #            Therefore possible updates in other models can still create sync jobs which is the
        #            intended and correct behaviour!
        if not create_sync_job:
            self = self.with_context(create_sync_job=True)

        # Create the sync Job
        if create_sync_job:
            sosync_write_date = self._sosync_write_date_now()
            for record in self:
                record.create_sync_job(sosync_write_date=sosync_write_date, job_source_type="delete")

        # Continue with the unlink method
        return super(BaseSosync, self).unlink()
