# -*- coding: utf-'8' "-*-"
import logging
from openerp import api, models, fields
from openerp.addons.fso_base.tools.validate import is_valid_url
import requests
from requests import Session
import timeout_decorator

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

    # FIELDS
    # SyncJob Basics
    job_id = fields.Integer(string="Sosync Job ID", readonly=True)
    job_date = fields.Datetime(string="Job Date", default=fields.Datetime.now(), readonly=True)
    fetched = fields.Datetime(string="Fetched Date", readonly=True)
    start = fields.Datetime(string="Start", readonly=True)
    end = fields.Datetime(string="End", readonly=True)
    duration = fields.Integer(string="Duration (ms)", compute='_job_duration', readonly=True)
    run_count = fields.Integer(string="Run Count", readonly=True)
    # HINT: If a sync job is related to a flow listed in the instance pillar option "sosync_skipped_flows"
    #       the job and any related parent-job will get the state "skipped" from the sosyncer service
    state = fields.Selection(selection=[("new", "New"),
                                        ("inprogress", "In Progress"),
                                        ("done", "Done"),
                                        ("error", "Error"),
                                        ("skipped", "Skipped")],
                             string="State", default="new", readonly=True)
    error_code = fields.Selection(selection=[("timeout", "Job timed out"),
                                             ("run_counter", "Run count exceeded"),
                                             ("child_job_creation", "Child job creation error"),
                                             ("child_job_processing", "Child job processing error"),
                                             ("source_data", "Source data error"),
                                             ("target_request", "Target request error"),
                                             ("cleanup", "Job finalization error")],
                                  string="Error Code", readonly=True)
    error_text = fields.Text(string="Error", readonly=True)

    # ChildJobs
    parent_job_id = fields.Integer(string="Parent Job ID", help="Parent Job ID (from field job_id)", readonly=True)
    parent_id = fields.Many2one(comodel_name="sosync.job", string="Parent Job", readonly=True)
    child_ids = fields.One2many(comodel_name="sosync.job", inverse_name="parent_id", string="Child Jobs", readonly=True)
    child_start = fields.Datetime(string="Child Processing Start", readonly=True)
    child_end = fields.Datetime(string="Child Processing End", readonly=True)
    child_duration = fields.Integer(string="Child Processing Duration", compute="_child_duration", readonly=True)

    # SyncJob Source
    source_system = fields.Selection(selection=_systems, string="Source System", readonly=True)
    source_model = fields.Char(string="Source Model", readonly=True)
    source_record_id = fields.Integer(string="Source Record ID", readonly=True)

    # SyncJob Target
    # ATTENTION: Calculated during job processing by its SyncFlow based on write_date (or existence) of the records.
    # HINT: target_model always shows only the "main model" even if the SyncFlow updates multiple models in the target.
    target_system = fields.Selection(selection=_systems, string="Target System", readonly=True)
    target_model = fields.Char(string="Target Model", readonly=True)
    target_record_id = fields.Integer(string="Target Record ID", readonly=True)

    # SyncJob Synchronization
    source_data = fields.Text(string="Source Data", readonly=True)
    target_request = fields.Text(string="Target Request(s)", readonly=True)
    target_request_start = fields.Datetime(string="Target Request(s) Start", readonly=True)
    target_request_end = fields.Datetime(string="Target Request(s) End", readonly=True)
    target_request_duration = fields.Integer(string="Target Request(s) Duration (ms)",
                                             compute="_target_request_duration", readonly=True)
    target_request_answer = fields.Text(string="Target Request(s) Answer(s)", readonly=True)

    # SyncJob Fetching


    # COMPUTED FIELDS METHODS
    @api.depends('start', 'end')
    def _job_duration(self):
        for rec in self:
            if rec.start and rec.end:
                rec.duration = _duration_in_ms(rec.start, rec.end)

    @api.depends('target_request_start', 'target_request_end')
    def _target_request_duration(self):
        for rec in self:
            if rec.target_request_start and rec.target_request_end:
                rec.duration = _duration_in_ms(rec.target_request_start, rec.target_request_end)

    @api.depends('child_start', 'child_end')
    def _child_duration(self):
        for rec in self:
            if rec.child_start and rec.child_end:
                rec.child_duration = _duration_in_ms(rec.child_start, rec.child_end)


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
    date = fields.Datetime(readonly=False)
    source_system = fields.Selection(readonly=False)
    source_model = fields.Char(readonly=False)
    source_record_id = fields.Integer(readonly=False)

    state = fields.Selection(selection_add=([("submitted", "Submitted"),
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
    def submit_sync_job(self, instance="", url="", http_header={}, crt_pem="", prvkey_pem="", user="", pwd=""):
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
                response = session.get(url, headers=http_header, timeout=12,
                                       params={'job_date': record.job_date,
                                               'source_system': record.source_system,
                                               'source_model': record.source_model,
                                               'source_record_id': record.source_record_id})
            except Exception as e:
                record.sudo().write({'state': 'submission_failed',
                                     'submission': submission,
                                     'submission_error': 'error',
                                     'submission_response_body': "GET Request Exception:\n%s" % e})
                # Continue with next record
                continue

            # HTTP Error Code returned
            if response.status_code != requests.codes.ok:
                record.sudo().write({'state': 'submission_failed',
                                     'submission': submission,
                                     'submission_error': 'error',
                                     'submission_response_code': response.status_code,
                                     'submission_response_body': response.content})
                # Continue with next record
                continue

            # Submission was successful
            record.sudo().write({'state': 'submitted',
                                 'submission': submission,
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
        new_jobs_in_queue = self.search([('state', '=', 'new')], limit=limit)

        # Submit jobs to sosync service
        if new_jobs_in_queue:
            new_jobs_in_queue.submit_sync_job()
        else:
            logger.info("No sosync sync-jobs in queue to submit!")


# NEW ABSTRACT MODEL: base.sosync
# Use this for all models where yout want to enable sosync sync job creation
class BaseSosync(models.AbstractModel):
    _name = "base.sosync"

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
                                    "state": "new",
                                    "source_system": "fso",
                                    "source_model": model,
                                    "source_record_id": record.id,
                                    })
            logger.info("Sosync SyncJob %s created for %s with id %s in queue!" % (job.id, model, record.id))

    @api.multi
    def write(self, values, create_sync_job=True):
        # Perform original write
        result = super(BaseSosync, self).write(values)

        # CREATE SYNC JOBS
        field_dict = values or dict()

        # HINT: Switch in context dict to suppress sync job generation
        #       This is mandatory for all updates from the sosyncer service to avoid endless sync job generation
        # ATTENTION: "create_sync_job" is not passed on to subsequent writes!
        #            Therefore possible updates in other models can still create sync jobs which is the intended
        #            behaviour!
        if create_sync_job:
            # Check for sosync tracked fields
            if any(field_key in field_dict for field_key in self._get_sosync_tracked_fields()):
                self.create_sync_job()

        # Continue with write method
        return result
