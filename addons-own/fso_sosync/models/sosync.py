# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields
# Try to extend MAGIC_COLUMNS with sosync fields to make sure they will not be copied and so on :)
# ATTENTION: This is a test! It is not clear if adding the sosync fields to the magic columns will have side effects!
from openerp.models import MAGIC_COLUMNS

from dateutil import parser
import datetime
import json

import logging
logger = logging.getLogger(__name__)


# HELPER FUNCTIONS
def _duration_in_ms(start_datetime, end_datetime):
    try:
        duration = parser.parse(end_datetime) - parser.parse(start_datetime)
        return int(duration.total_seconds() * 1000)
    except:
        pass
    return None


# NEW ABSTRACT MODEL: base.sosync
# Use this for all models where you want to enable sosync sync job creation
class BaseSosync(models.AbstractModel):
    _name = "base.sosync"

    # NEW COMMON FIELDS
    sosync_fs_id = fields.Integer(string="Fundraising Studio ID", readonly=True, index=True)
    sosync_write_date = fields.Char(string="Sosync Write Date", readonly=True, index=True,
                                    help="Last change of one or more sosync-tracked-fields.")
    # HINT: Is a char field to show exact ms
    sosync_sync_date = fields.Char(string="Last sosync sync", readonly=True,
                                   help="Exact datetime of source-data-readout for the sync job!")

    # Extend MAGIC_COLUMNS to make sure these fields are NOT copied if a record is copied!
    # ATTENTION: It is unclear if there are any unwanted side effects!
    logger.warning("base.sosync MAGIC_COLUMNS before: %s" % MAGIC_COLUMNS)
    MAGIC_COLUMNS += ['sosync_fs_id', 'sosync_write_date', 'sosync_sync_date']
    logger.warning("base.sosync MAGIC_COLUMNS after: %s" % MAGIC_COLUMNS)

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

        # If the fields are already stored for this model there is no need to recompute them
        if not getattr(self, '_sosync_tracked_fields', False):

            for name, field in self._fields.items():
                if getattr(field, 'sosync', False) or name in updated_fields:
                    sosync_tracked_fields.append(name)

            self._sosync_tracked_fields = sosync_tracked_fields

        return self._sosync_tracked_fields

    @api.model
    def _sosync_watched_fields(self, values={}):
        if not values:
            return dict()

        tracked_fields = self._get_sosync_tracked_fields()
        try:
            watched_fields = {key: str(values[key]) for key in values if key in tracked_fields}
        except Exception as e:
            logger.error("_sosync_watched_fields: %s" % repr(e))
            watched_fields = {key: values[key] for key in values if key in tracked_fields}
            pass
        return watched_fields

    @api.model
    def _sosync_watched_fields_json(self, watched_fields):
        # Convert watched_fields dict to json formatted string
        try:
            watched_fields_json = json.dumps(watched_fields, ensure_ascii=False)
        except Exception as e:
            logger.error("Could not convert watched_fields to json! %s" % repr(e))
            watched_fields_json = watched_fields
            pass
        return watched_fields_json

    @api.multi
    def create_sync_job(self, job_date=False, sosync_write_date=False,
                        job_priority=False,
                        job_source_fields=False,
                        job_source_type=False,
                        job_source_merge_into_record_id=False,
                        job_source_target_merge_into_record_id=False):
        # HINT: sosync_write_date may be emtpy for initial sync of records sosync v2 uses write date as a fallback
        # HINT: job_source_fields may be empty by sync job creation in gui
        job_date = job_date or fields.Datetime.now()
        job_queue = self.env["sosync.job.queue"].sudo()
        model = self._name

        # Try to get job_priority from the model if not in kwargs
        if not job_priority:
            job_priority = getattr(self, '_sync_job_priority', False)

        # Create sync jobs
        for record in self:
            sosync_write_date = sosync_write_date or record.sosync_write_date

            # Create job values
            job_values = {"job_date": job_date,
                          "job_source_system": "fso",
                          "job_source_model": model,
                          "job_source_record_id": record.id,
                          "job_source_target_record_id": record.sosync_fs_id,
                          "job_source_sosync_write_date": sosync_write_date,
                          "job_source_fields": job_source_fields,
                          "job_source_type": job_source_type,
                          "job_source_merge_into_record_id": job_source_merge_into_record_id,
                          "job_source_target_merge_into_record_id": job_source_target_merge_into_record_id,
                          }

            # Add job_priority to job values if given by kwargs or context
            # HINT: If not set in kwargs the default value of the field is taken which is 1000
            if job_priority:
                job_values['job_priority'] = job_priority

            # Create the sync job in the queue (sosync.job.queue)
            job = job_queue.create(job_values)
            logger.debug("Sosync SyncJob %s created for %s with id %s in queue!" % (job.id, model, record.id))

        return True

    @api.model
    def create(self, values, **kwargs):
        # CREATE SYNC JOBS
        # ----------------
        values = values or dict()

        # Get value of _sync_job_priority if it is in vals and remove it from vals so that the record can be
        # created correctly
        job_priority = values.pop('_sync_job_priority', False)

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

        # Get all watched fields for this model based on the fields in values
        watched_fields = self._sosync_watched_fields(values)
        watched_fields_json = self._sosync_watched_fields_json(watched_fields)

        # Get the sosync_write_date string
        sosync_write_date = self._sosync_write_date_now()

        # Add sosync_write_date to the values of the record to create if a sync job generation should happen
        if create_sync_job and watched_fields:
            values["sosync_write_date"] = sosync_write_date

        # Create the record
        rec = super(BaseSosync, self).create(values, **kwargs)

        # Create the sync job for the new (in memory only right now) record
        if rec:
            if create_sync_job and watched_fields:

                # Create sync job
                rec.create_sync_job(sosync_write_date=sosync_write_date,
                                    job_source_fields=watched_fields_json,
                                    job_priority=job_priority)

        return rec

    @api.multi
    def write(self, values, **kwargs):
        # CREATE SYNC JOBS
        # ----------------
        values = values or dict()

        # Get value of _sync_job_priority if it is in vals and remove it from vals so that the record can be
        # written (updated) correctly
        job_priority = values.pop('_sync_job_priority', False)

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

        # Get all watched fields for this model based on the fields in values
        watched_fields = self._sosync_watched_fields(values)
        watched_fields_json = self._sosync_watched_fields_json(watched_fields)

        # Update the record and add the new sosync_write_date and then create the sync jobs
        if create_sync_job and watched_fields:

            # Get the sosync_write_date string
            sosync_write_date = self._sosync_write_date_now()

            # Add sosync_write_date to the values for the records to update
            values["sosync_write_date"] = sosync_write_date

            # Update the records (including new value of 'sosync_write_date' field)
            res = super(BaseSosync, self).write(values, **kwargs)

            # Create the sync jobs for the records
            self.create_sync_job(sosync_write_date=sosync_write_date,
                                 job_source_fields=watched_fields_json,
                                 job_priority=job_priority)

        # Update record without sync job and sosync_write_date
        else:
            res = super(BaseSosync, self).write(values, **kwargs)

        # Continue with write method
        return res

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
            self.create_sync_job(sosync_write_date=sosync_write_date, job_source_type="delete")

        # Continue with the unlink method
        return super(BaseSosync, self).unlink()
