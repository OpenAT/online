# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from sosync import _duration_in_ms

import datetime
import logging
logger = logging.getLogger(__name__)


# ATTENTION: This class is deprecated because sync jobs will be stored in the sosync_gui databases only!
class SosyncJob(models.Model):
    """
    sosync sync jobs

    A sync job is basically just a signal that a record had some relevant changes. Directions and final sync
    behaviour is determined by the sync flow!

    ATTENTION: !!! This is deprecated because sync jobs will be stored in the sosync_gui databases only !!!
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
    job_priority = fields.Integer(string="Job Priority", default=1000, readonly=True,
                                  help="A greater number means a higher priority!")
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

    # -----------------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED JOB QUEUE CLEANUP
    # -----------------------------------------------
    @api.model
    def delete_old_jobs(self):
        delete_before = datetime.datetime.now() - datetime.timedelta(days=90)
        delete_before = delete_before.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        domain = [('write_date', '<=', delete_before),
                  ('job_state', 'in', ['done', 'skipped'])]
        jobs_to_delete = self.search(domain, limit=1)
        if jobs_to_delete:
            # TODO: Change this to custom SQL code for performace
            #       1.) Delete (and backup for restore) the indexes
            #       2.) Disable any triggers on the table
            #       3.) Delete the rows by sql with the domain (select) from above
            #       4.) Restore the indexes
            #       5.) Enable the trigger
            logger.warning("Found %s sync jobs for cleanup" % len(jobs_to_delete))
            jobs_to_delete.unlink()

