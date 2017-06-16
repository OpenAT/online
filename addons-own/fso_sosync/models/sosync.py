# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields


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
    date = fields.Datetime(string="Job Creation Time")
    start = fields.Datetime(string="Job Start")
    end = fields.Datetime(string="Job End")
    duration = fields.Integer(string="Job Duration (ms)", compute='_job_duration')
    state = fields.Selection(selection=[("new", "New"),
                                        ("inprogress", "In Progress"),
                                        ("done", "Done"),
                                        ("error", "Error")],
                             string="State")
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

    # COMPUTED FIELDS METHODS
    @api.depends('end')
    def _job_duration(self):
        for rec in self:
            if rec.start and rec.end:
                rec.duration = _duration_in_ms(rec.start, rec.end)

    @api.depends('target_request_end')
    def _target_request_duration(self):
        for rec in self:
            if rec.target_request_start and rec.target_request_end:
                rec.duration = _duration_in_ms(rec.target_request_start, rec.target_request_end)

    @api.depends('child_end')
    def _child_duration(self):
        for rec in self:
            if rec.child_start and rec.child_end:
                rec.child_duration = _duration_in_ms(rec.child_start, rec.child_end)


class SosyncJobQueue(models.Model):
    """
    This is the queue of jobs that will be fetched by the sosyncer from FS-Online on every run.
    Jobs that are successfully fetched will be marked done.
    HINT: Fetched jobs older than one month will be removed by an automated action.
    """
    _name = 'sosync.job.queue'
    _inherit = 'sosync.job'

    # FIELDS
    job_fetched = fields.Datetime(string="Job Fetched")
