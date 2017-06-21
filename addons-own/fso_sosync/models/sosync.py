# -*- coding: utf-'8' "-*-"
import logging
from openerp import api, models, fields

logger = logging.getLogger(__name__)


# HELPER FUNCTIONS
def _duration_in_ms(start_datetime, end_datetime):
    duration = end_datetime - start_datetime
    return int(duration.total_seconds() * 1000)


class SosyncJob(models.Model):
    """
    sosync sync jobs
    """
    _name = 'sosync.job'

    # CONSTANTS
    _systems = [("fso", "FS-Online"), ("fs", "Fundraising Studio")]

    # FIELDS
    # SyncJob Basics
    job_id = fields.Integer(string="Job ID")
    date = fields.Datetime(string="Creation")
    job_fetched = fields.Datetime(string="Fetched")
    start = fields.Datetime(string="Start")
    end = fields.Datetime(string="End")
    duration = fields.Integer(string="Duration (ms)", compute='_job_duration')
    run_count = fields.Integer(string="Run Count")
    # HINT: If a sync job is related to a flow listed in the instance pillar option "sosync_skipped_flows"
    #       the job and any related parent-job will get the state "skipped" from the sosyncer service
    state = fields.Selection(selection=[("new", "New"),
                                        ("inprogress", "In Progress"),
                                        ("done", "Done"),
                                        ("error", "Error"),
                                        ("skipped", "Skipped")],
                             string="State", default="new")
    error_code = fields.Selection(selection=[("timeout", "Job timed out"),
                                             ("run_counter", "Run count exceeded"),
                                             ("child_job_creation", "Child job creation error"),
                                             ("child_job_processing", "Child job processing error"),
                                             ("source_data", "Source data error"),
                                             ("target_request", "Target request error"),
                                             ("cleanup", "Job finalization error")],
                                  string="Error Code")
    error_text = fields.Text(string="Error")

    # ChildJobs
    parent_job_id = fields.Integer(string="Parent Job ID", help="Parent Job ID (from field job_id)")
    parent_id = fields.Many2one(comodel_name="sosync.job", string="Parent Job")
    child_ids = fields.One2many(comodel_name="sosync.job", inverse_name="parent_id", string="Child Jobs")
    child_start = fields.Datetime(string="Child Processing Start")
    child_end = fields.Datetime(string="Child Processing End")
    child_duration = fields.Integer(string="Child Processing Duration", compute="_child_duration")

    # SyncJob Source
    source_system = fields.Selection(selection=_systems, string="Source System")
    source_model = fields.Char(string="Source Model")
    source_record_id = fields.Integer(string="Source Record ID")

    # SyncJob Target
    # ATTENTION: Calculated during job processing by its SyncFlow based on write_date (or existence) of the records.
    # HINT: target_model always shows only the "main model" even if the SyncFlow updates multiple models in the target.
    target_system = fields.Selection(selection=_systems, string="Target System")
    target_model = fields.Char(string="Target Model")
    target_record_id = fields.Integer(string="Target Record ID")

    # SyncJob Synchronization
    source_data = fields.Text(string="Source Data")
    target_request = fields.Text(string="Target Request(s)")
    target_request_start = fields.Datetime(string="Target Request(s) Start")
    target_request_end = fields.Datetime(string="Target Request(s) End")
    target_request_duration = fields.Integer(string="Target Request(s) Duration (ms)",
                                             compute="_target_request_duration")
    target_request_answer = fields.Text("Target Request(s) Answer(s)")

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


class SosyncJobQueue(models.Model):
    """
    This is the queue of jobs that needs to be submitted to the sosyncer.
    Submission is done by a simple REST URL call to the sosyncer with the fields source_system, source_model and
    and source_record_id.
    Example: http://sosync.care.datadialog.net?source_system=fso&source_model=res
    """
    _name = 'sosync.job.queue'
    _inherit = 'sosync.job'

    state = fields.Selection(selection_add=([("submitted", "Submitted"), ("submission_failed", "Submission Failed")]))

    submission = fields.Datetime(string="Submission")
    submission_response_code = fields.Char(string="Response Code", help="HTTP Response Code")
    submission_response_body = fields.Text(string="Response Body")

    submission_error = fields.Selection(selection=[("timeout", "Request timed out"),
                                                   ("not_available", "Service not available"),
                                                   ("error", "Request error")],
                                        string="Submission Error")


# Abstract sosyncer mixin
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
            job = job_queue.create({"date": date,
                                    "state": "new",
                                    "source_system": "fso",
                                    "source_model": model,
                                    "source_record_id": record.id,
                                    })
            logger.info("Sosync SyncJob %s created for %s with id %s" % (job.id, model, record.id))

    # METHODS
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
