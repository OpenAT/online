# -*- coding: utf-'8' "-*-"
import logging
from openerp import api, models, fields
from openerp.addons.fso_base.tools.validate import is_valid_url
import requests
from requests import Session

logger = logging.getLogger(__name__)


# CUSTOM EXCEPTION CLASSES
class GenericTimeoutError(Exception):
    def __init__(self):
        Exception.__init__(self, "Execution stopped because of global timeout and not the request.Session() timeout!"
                                 "There may be a passphrase in your private key.")


# HELPER FUNCTIONS
def _duration_in_ms(start_datetime, end_datetime):
    duration = end_datetime - start_datetime
    return int(duration.total_seconds() * 1000)


# NEW ODOO MODEL: sosync.job
class SosyncJob(models.Model):
    """
    sosync sync jobs
    """
    _name = 'sosync.job'

    # CONSTANTS
    _systems = [("fso", "FS-Online"), ("fs", "Fundraising Studio")]

    # ======
    # FIELDS
    # ======

    # SYNCJOB
    job_id = fields.Integer(string="Sosync Job ID", readonly=True)
    job_date = fields.Datetime(string="Job Date", default=fields.Datetime.now(), readonly=True)

    # SYNCJOB SOURCE
    job_source_system = fields.Selection(selection=_systems, string="Source System", readonly=True)
    job_source_model = fields.Char(string="Source Model", readonly=True)
    job_source_record_id = fields.Integer(string="Source Record ID", readonly=True)

    # SYNCJOB INFO
    job_fetched = fields.Datetime(string="Fetched Date", readonly=True)
    job_start = fields.Datetime(string="Start", readonly=True)
    job_end = fields.Datetime(string="End", readonly=True)
    job_duration = fields.Integer(string="Duration (ms)", compute='_job_duration', readonly=True)
    job_run_count = fields.Integer(string="Run Count", readonly=True,
                                   help="Restarts triggered by changed source data in between job processing")
    # HINT: If a sync job is related to a flow listed in the instance pillar option "sosync_skipped_flows"
    #       the job and any related parent-job will get the state "skipped" from the sosyncer service
    job_state = fields.Selection(selection=[("new", "New"),
                                            ("inprogress", "In Progress"),
                                            ("child", "ChildJob Processing"),
                                            ("done", "Done"),
                                            ("error", "Error"),
                                            ("skipped", "Skipped")],
                                 string="State", default="new", readonly=True)
    job_error_code = fields.Selection(selection=[("timeout", "Job timed out"),
                                             ("run_counter", "Run count exceeded"),
                                             ("child_job_creation", "Child job creation error"),
                                             ("child_job_processing", "Child job processing error"),
                                             ("source_data", "Sync Source error"),
                                             ("target_request", "Sync Target error"),
                                             ("cleanup", "Job finalization error")],
                                  string="Error Code", readonly=True)
    job_error_text = fields.Text(string="Error", readonly=True)
    job_log = fields.Text(string="Job Log", readonly=True)

    # PARENT JOB
    parent_job_id = fields.Integer(string="Parent Job ID", help="Parent Job ID (from field job_id)", readonly=True)

    # ODOO ONLY (to show a hierarchy view later on in the odoo gui)
    #           (TODO: must be computed fields based on job id and parent_job_id)
    parent_job_odoo = fields.Many2one(comodel_name="sosync.job", string="Parent Job", readonly=True)
    child_jobs_odoo = fields.One2many(comodel_name="sosync.job", inverse_name="parent_job_odoo", string="Child Jobs",
                                      readonly=True)

    # CHILD JOBS PROCESSING TIME
    child_job_start = fields.Datetime(string="Child Processing Start", readonly=True)
    child_job_end = fields.Datetime(string="Child Processing End", readonly=True)
    child_job_duration = fields.Integer(string="Child Processing Duration", compute="_child_duration", readonly=True)

    # SYNCHRONIZATION SOURCE
    sync_source_system = fields.Selection(selection=_systems, string="Source System", readonly=True)
    sync_source_model = fields.Char(string="Source Model", readonly=True)
    sync_source_record_id = fields.Integer(string="Source Record ID", readonly=True)

    # SYNCHRONIZATION TARGET
    sync_target_system = fields.Selection(selection=_systems, string="Target System", readonly=True)
    sync_target_model = fields.Char(string="Target Model", readonly=True)
    sync_target_record_id = fields.Integer(string="Target Record ID", readonly=True)

    # SYNCHRONIZATION INFO
    sync_source_data = fields.Text(string="SYNC SOURCE Data", readonly=True)
    sync_target_request = fields.Text(string="SYNC TARGET Request(s)", readonly=True)
    sync_target_answer = fields.Text(string="SYNC TARGET Answer(s)", readonly=True)

    # SYNCHRONIZATION PROCESSING TIME
    sync_start = fields.Datetime(string="SYNC Start", readonly=True)
    sync_end = fields.Datetime(string="SYNC End", readonly=True)
    sync_duration = fields.Integer(string="SYNC Duration (ms)",
                                   compute="_target_request_duration", readonly=True)



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


# NEW ODOO MODEL: sosync.job.queue
class SosyncJobQueue(models.Model):
    """
    This is the queue of jobs that needs to be submitted to the sosyncer.
    Submission is done by a simple REST URL call to the sosyncer with the fields source_system, source_model and
    and source_record_id.
    Example: http://sosync.care.datadialog.net?source_system=fso&source_model=res
    """
    _name = 'sosync.job.queue'
    _inherit = 'sosync.job'

    # FIELDS
    # Remove of readonly attribute for testing purposes and manual sync job creation in the queue
    job_date = fields.Datetime(readonly=False)
    job_source_system = fields.Selection(readonly=False)
    job_source_model = fields.Char(readonly=False)
    job_source_record_id = fields.Integer(readonly=False)

    # Add new Fields only suitable for the queue
    job_state = fields.Selection(selection_add=([("submitted", "Submitted"),
                                                 ("submission_failed", "Submission Failed")]),
                                 readonly=True)

    submission = fields.Datetime(string="Submission", readonly=True)
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
        # Instance ID from first company (e.g.: care)
        instance = instance or self.env['res.company'].sudo().search([], limit=1).instance_id
        assert instance, "Instance ID for the default (first) company is missing!"

        # Sosync service url (in internal network)
        url = url or "http://sosync."+instance+".datadialog.net/job/create"
        is_valid_url(url=url, dns_check=False)

        # Create a Session Object (just like a regular UA e.g. Firefox or Chrome)
        session = Session()
        session.verify = True
        if crt_pem and prvkey_pem:
            session.cert = (crt_pem, prvkey_pem)
        if user and pwd:
            session.auth(user, pwd)

        # Submit every sync Job as a REST URL call to the sosyncer
        for record in self:
            logger.info("Submitting sosync sync-job %s from queue to %s!" % (record.id, url))
            submission = fields.Datetime.now()
            try:
                response = session.get(url, headers=http_header, timeout=timeout,
                                       params={'job_date': record.job_date,
                                               'job_source_system': record.job_source_system,
                                               'source_model': record.job_source_model,
                                               'source_record_id': record.job_source_record_id})
            except Exception as e:
                record.sudo().write({'job_state': 'submission_failed',
                                     'submission': submission,
                                     'submission_error': 'error',
                                     'submission_response_code': '',
                                     'submission_response_body': "GET Request Exception:\n%s" % e})
                # Continue with next record
                continue

            # HTTP Error Code returned
            if response.status_code != requests.codes.ok:
                record.sudo().write({'job_state': 'submission_failed',
                                     'submission': submission,
                                     'submission_error': 'error',
                                     'submission_response_code': response.status_code,
                                     'submission_response_body': response.content})
                # Continue with next record
                continue

            # Submission was successful
            record.sudo().write({'job_state': 'submitted',
                                 'submission': submission,
                                 'submission_error': '',
                                 'submission_response_code': response.status_code,
                                 'submission_response_body': response.content})

        return

    # --------------------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED JOB QUEUE SUBMISSION
    # --------------------------------------------------
    @api.model
    def scheduled_job_queue_submission(self, limit=60):
        logger.info("Scheduled sosync sync-job-queue submission!")

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
        if scheduled_action and scheduled_action.interval_type in interval_to_seconds:
            limit = int(scheduled_action.interval_number * interval_to_seconds[scheduled_action.interval_type])
            limit = 1 if limit <= 0 else limit

        # Search for new sync jobs to submit
        new_jobs_in_queue = self.search([('job_state', '=', 'new')], limit=limit)

        # Submit jobs to sosync service
        if new_jobs_in_queue:
            new_jobs_in_queue.submit_sync_job()
        else:
            logger.info("No sosync sync-jobs in queue to submit!")


# NEW ABSTRACT MODEL: base.sosync
# Use this for all models where yout want to enable sosync sync job creation
class BaseSosync(models.AbstractModel):
    _name = "base.sosync"

    # NEW COMMON FIELDS
    sosync_fs_id = fields.Integer(string="Fundraising Studio ID", readonly=True)
    sosync_write_date = fields.Datetime(string="Sosync Write Date", readonly=True,
                                        help="Last change of one or more sosync-tracked-fields.")
    # HINT: Is a char field to show exact ms
    sosync_sync_date = fields.Char(string="Last sosync sync", readonly=True,
                                   help="Exact datetime of source-data-readout for the sync job!")

    @api.model
    def _get_sosync_tracked_fields(self, updated_fields=list()):
        sosync_tracked_fields = list()

        for name, field in self._fields.items():
            if getattr(field, 'sosync', False) or name in updated_fields:
                sosync_tracked_fields.append(name)

        return sosync_tracked_fields

    @api.multi
    def create_sync_job(self):
        # Get the sosync.job.queue model in a new environment with the su user
        job_queue = self.env["sosync.job.queue"].sudo()
        date = fields.Datetime.now()
        model = self._name
        for record in self:
            job = job_queue.create({"job_date": date,
                                    "job_state": "new",
                                    "job_source_system": "fso",
                                    "job_source_model": model,
                                    "job_source_record_id": record.id,
                                    })
            logger.info("Sosync SyncJob %s created for %s with id %s in queue!" % (job.id, model, record.id))

    @api.multi
    def write(self, values, create_sync_job=True):
        # Perform original write
        result = super(BaseSosync, self).write(values)

        # CREATE SYNC JOBS
        # ----------------
        # HINT: Switch in context dict to suppress sync job generation
        #       This is mandatory for all updates from the sosyncer service to avoid endless sync job generation
        # ATTENTION: "create_sync_job" is not passed on to subsequent writes!
        #            Therefore possible updates in other models can still create sync jobs which is the intended
        #            behaviour!
        field_dict = values or dict()
        if create_sync_job:
            # Check for sosync tracked fields
            if any(field_key in field_dict for field_key in self._get_sosync_tracked_fields()):
                # Create Sync Job
                self.create_sync_job()
                # Update sosync_write_date
                for record in self:
                    record.sosync_write_date = fields.datetime.now()

        # Continue with write method
        return result
