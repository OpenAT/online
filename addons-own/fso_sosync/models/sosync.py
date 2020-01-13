# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields
from openerp.tools import SUPERUSER_ID
# Try to extend MAGIC_COLUMNS with sosync fields to make sure they will not be copied and so on :)
# ATTENTION: This is a test! It is not clear if adding the sosync fields to the magic columns will have side effects!
from openerp.models import MAGIC_COLUMNS

from dateutil import parser
import datetime
import json
import sys

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

    # ATTENTION: DO NOT ALTER THE MAGIC FIELD OR IT WILL LEAD TO UNDESIRED SIDE EFFECTS
    #            ALTER copy_data instead as done below in this file !!!
    # Extend MAGIC_COLUMNS to make sure these fields are NOT copied if a record is copied!
    # ATTENTION: It is unclear if there are any unwanted side effects!
    # logger.warning("base.sosync MAGIC_COLUMNS before: %s" % MAGIC_COLUMNS)
    # MAGIC_COLUMNS += ['sosync_fs_id', 'sosync_write_date', 'sosync_sync_date']
    # logger.warning("base.sosync MAGIC_COLUMNS after: %s" % MAGIC_COLUMNS)

    def init(self, cr, context=None):

        ir_actions_server_obj = self.pool.get('ir.actions.server')
        ir_values_obj = self.pool.get('ir.values')

        model_name = self._name
        model_id = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', model_name)])[0]
        # model_id_test = self.ref('model_'+model_name.replace('.', '_'))

        server_action_name = 'Manually Create Sync Job'
        more_menu_name = server_action_name

        if model_name != 'base.sosync':
            logger.info("base.sosync init: Create action in 'More' menu to manually create sync jobs for model %s"
                        "" % self._name)
            server_action = ir_actions_server_obj.search(cr, SUPERUSER_ID,
                                                         [('name', '=', server_action_name),
                                                          ('model_id', '=', model_id),
                                                          ('state', '=', 'code')])
            if server_action:
                assert len(server_action) <= 1, "More than one server action found!"
                logger.info("base.sosync init: Deleting server action %s for recreation!" % server_action)
                # ir_actions_server_obj.unlink(cr, SUPERUSER_ID, server_action)
                # server_action = False

            # Create server_action
            if not server_action:
                logger.info("base.sosync init: create server action '%s'" % server_action_name)
                server_action = ir_actions_server_obj.create(cr, SUPERUSER_ID,
                                                             {'name': server_action_name,
                                                              'model_id': model_id,
                                                              'state': 'code',
                                                              'code': """
                    if context.get('active_model') == '%s':
                    
                        # Find ids
                        ids = []
                        
                        #if context.get('active_domain'):
                        #    ids = self.search(cr, uid, context['active_domain'], context=context)
                        #elif context.get('active_ids'):
                        #    ids = context['active_ids']
                        
                        if context.get('active_ids'):
                            ids = context['active_ids']
                    
                        # Call button action action_set_bpk
                        if ids:
                            self.create_sync_job_manually(cr, uid, ids, context=context)                                                              
                                                              """ % model_name})
                server_action_id = server_action
            else:
                logger.info("base.sosync init: server action exists")
                server_action_id = server_action[0]

            # Create 'More' menu entry
            more_menu = ir_values_obj.search(cr, SUPERUSER_ID,
                                             [('name', '=', more_menu_name),
                                              ('model', '=', model_name),
                                              ('key2', '=', 'client_action_multi'),
                                              ('value', '=', 'ir.actions.server,%s' % str(server_action_id))])
            if not more_menu:
                logger.info("base.sosync init: create ir.values entry '%s' for more menu" % more_menu_name)
                ir_values_obj.create(cr, SUPERUSER_ID, {
                    'name': more_menu_name,
                    'model': model_name,
                    'key2': 'client_action_multi',
                    'value': 'ir.actions.server,%s' % str(server_action_id)
                })

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

    @staticmethod
    def _sosync_write_date_now():
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
        watched_fields = dict()
        if not values:
            return watched_fields

        # Get all tracked fields
        tracked_fields = self._get_sosync_tracked_fields()

        # Get watched_fields and val data
        for f_name, val in values.iteritems():
            if f_name in tracked_fields:
                # Do not store binary field data
                try:
                    if self._fields[f_name].type == 'binary':
                        val = 'binary data'
                except:
                    pass

                # Convert to string
                try:
                    val = str(val)
                except:
                    try:
                        val = json.dumps(val, ensure_ascii=False)
                    except:
                        val = 'Could not convert to string'

                # Skipp long strings
                try:
                    if len(val) > 64:
                        val = val[0:63] + ' ...too large to log'
                except:
                    val = 'could not check size, logging skipped'

                # Append to watched_fields
                watched_fields[f_name] = val

        return watched_fields

    @staticmethod
    def _sosync_watched_fields_json(watched_fields):
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

    @api.multi
    def create_sync_job_manually(self):
        """
        Manually create regular (job_source_type=False) sync jobs!
        HINT: This will only work if the record has already a sosync_write_date!
        :return:
        """
        for record in self:
            if record.sosync_write_date:
                record.create_sync_job(job_date=record.sosync_write_date,
                                       job_source_type=False, job_source_fields='Manually created!')

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

    # ATTENTION: _write() was used instead of write to catch stored computed field changes!
    # Computed fields that will be stored in the database will be recomputed by models.py > recompute() which will
    # call _write(). If we inherit _write instead of write we may get all relevant fields
    def _write(self, cr, user, ids, vals, context=None):
        vals = vals if vals else dict()
        context = context if context else dict()
        logger.debug("SOSYNCER _write(): self: %s, vals: %s, context: %s" % (str(repr(self)), str(vals), str(context)))

        # ----------------------
        # SYNC DATE AND SYNC JOB
        # ----------------------
        if 'sosync_write_date' not in vals:
            # Get sync-job-switch from context
            create_sync_job = context.get("create_sync_job", True)

            # TODO: Re-Enable sync-job-switch in context for all other models that may be called subsequently
            #       since context is a frozendict we should first check if this is ok or not ...
            # if not create_sync_job:
            #     context['create_sync_job'] = True

            # Get fields that are watched by the sosyncer
            watched_fields = self._sosync_watched_fields(cr, user, values=vals, context=context)

            # Check if watched data changed
            if create_sync_job and watched_fields:
                # Data changed therefore we create a new unique id for current watched data in form of a timestamp
                sosync_write_date = self._sosync_write_date_now()

                # Append the sosync_write_date
                vals["sosync_write_date"] = sosync_write_date

                # Create the sync jobs for the records
                recs = self.browse(cr, user, ids, context)
                logger.debug("SOSYNCER _write(): Create sync jobs for %s" % str(repr(recs)))
                recs.create_sync_job(sosync_write_date=sosync_write_date,
                                     job_source_fields=self._sosync_watched_fields_json(watched_fields),
                                     job_priority=vals.pop('_sync_job_priority', False))

        return super(BaseSosync, self)._write(cr, user, ids, vals, context=context)

    # REGULAR FIELDS
    # --------------
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
    def _create_comodel_delete_sync_jobs(self, sosync_write_date=False, models_done=tuple()):
        """
        Cascade deletes are not handled by the orm therefore no unlink method is called for them and no delete-sync-job
        would be generated. To partly overcome this limitation we search for all related one2many fields with
        ondelete="cascade" and create delete sync jobs for the comodel records linked through the field recursively!

        ATTENTION: This is not perfect and may not work for all cascade delete constellations but should cover most/all
                   of our (FRST) cases!

        :param sosync_write_date:
        :param models_done: tuple with the names of all models already done to avoid recursion!
        :return: bool
        """
        sosync_write_date = sosync_write_date or self._sosync_write_date_now()

        # Check if the self model name is already in models_done
        # TODO: Do not only use model_name for models_done but a combination of model and field name to avoid skipping
        #       models where multiple fields points to the same comodel.
        model_name = self._name
        if model_name not in models_done:
            models_done += (model_name,)

        if not hasattr(self, '_fields'):
            logger.warning("comodel_delete_sync_jobs() self has no attribute '_fields'!\n%s" % repr(self))
            return False

        # Check all one2many fields of this model for related many2one fields with ondelete="cascade"
        for f_name in self._fields:

            # Get the field object
            f = self._fields[f_name]

            # TODO: Since we know that we only check for one2many fields we may better check for this directly instead
            #       of 'comodel_name' and 'inverse_fields'?

            # Get the comodel object if it is a sosync model and append it's name to models_done
            comodel_name = False
            if comodel_name not in models_done:
                if hasattr(f, 'comodel_name') and f.comodel_name:
                    if hasattr(self.env[f.comodel_name], 'create_sync_job'):
                        comodel_name = f.comodel_name

            if comodel_name:

                # Check if the inverse field of an one2many field has ondelete='cascade' set
                if (hasattr(f, 'inverse_fields')
                        and f.inverse_fields and hasattr(f.inverse_fields[0], 'ondelete')
                        and f.inverse_fields[0].ondelete == 'cascade'):

                    # Now we know that the inverse many2one field has ondelete=cascade set therefore we need to create
                    # delete-sync-jobs for all the records linked in the one2many field
                    for r in self:
                        field_comodel_records = r[f.name]

                        if field_comodel_records:
                            # Create delete sync jobs for all records of the comodel
                            field_comodel_records.create_sync_job(sosync_write_date=sosync_write_date,
                                                                  job_source_type="delete")

                            # Recursively check for additional one2many fields in the comodel records also
                            field_comodel_records._create_comodel_delete_sync_jobs(sosync_write_date=sosync_write_date,
                                                                                   models_done=models_done)

        return True

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

        # Create the delete-sync-job(s)
        if create_sync_job:
            sosync_write_date = self._sosync_write_date_now()

            # Recursively get all records from one2many fields where the inverse many2one field has ondelete=cascade
            # and create delete_sync_jobs for those records also!
            self._create_comodel_delete_sync_jobs(sosync_write_date=sosync_write_date)

            # Create a delete sync job for all records
            self.create_sync_job(sosync_write_date=sosync_write_date, job_source_type="delete")

        # Continue with the unlink method
        return super(BaseSosync, self).unlink()

    # Remove sosync fields from data when a record is duplicated (copied) see copy_data() in models.py
    def copy_data(self, cr, uid, id, default=None, context=None):

        data_to_copy = super(BaseSosync, self).copy_data(cr, uid, id, default, context=context)

        # Remove sosync fields from data_to_copy
        for sosync_field in ('sosync_fs_id', 'sosync_write_date', 'sosync_sync_date'):
            data_to_copy.pop(sosync_field, None)

        return data_to_copy
