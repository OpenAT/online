# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields
from openerp.tools import SUPERUSER_ID

# ATTENTION: DO NOT ALTER THE MAGIC FIELD OR IT WILL LEAD TO UNDESIRED SIDE EFFECTS
#            ALTER copy_data instead as done below in this file !!!
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


# ATTENTION: DO NOT ALTER THE MAGIC FIELDS / MAGIC_COLUMNS OR IT WILL LEAD TO UNDESIRED SIDE EFFECTS
#            ALTER copy_data instead as done below in this file !!!
class BaseSosync(models.AbstractModel):
    """
    Add this abstract model to all models where want to create sosync jobs!
    """
    _name = "base.sosync"

    _sosyncer_fields = ('sosync_fs_id', 'sosync_write_date', 'sosync_synced_version',
                        'frst_create_date', 'frst_write_date')

    # NEW COMMON FIELDS
    sosync_fs_id = fields.Integer(string="Fundraising Studio ID", readonly=True, index=True, group_operator="count")
    sosync_write_date = fields.Char(string="Sosync Write Date", readonly=True, index=True,
                                    help="Last change of one or more sosync-tracked-fields. This is just like a "
                                         "'record version'! Could be replaced by a uniqe hash of the field data in the"
                                         "future.")
    
    # HINT: Is a char field to show exact ms
    sosync_synced_version = fields.Char(string="Last synced Version", readonly=True,
                                    help="The 'sosync_write_date' (which is the record-version) of the latest sync."
                                         "If this is different from the current 'sosync_write_date' unsynced changes "
                                         "happended since the last sync!\nIn case of changes in both systems at a sync "
                                         "We choose Fundraising Studio as the winner and force the direction 'From "
                                         "FRST to FSON'!")

    # Create and Write Date from Fundraising Studio
    frst_create_date = fields.Datetime(string="FRST Create Date", readonly=True)
    frst_write_date = fields.Datetime(string="FRST Write Date", readonly=True)

    # Create "more-menu" actions for manual sync job creation on update or installation of the addon
    def init(self, cr, context=None):
        ir_actions_server_obj = self.pool.get('ir.actions.server')
        ir_values_obj = self.pool.get('ir.values')

        model_name = self._name
        model_id = self.pool.get('ir.model').search(cr, SUPERUSER_ID, [('model', '=', model_name)])[0]

        server_action_name = 'Manually Create Sync Job'
        more_menu_name = server_action_name

        if model_name != 'base.sosync':
            logger.info("base.sosync init: Create action in 'More' menu to manually create sync jobs for model %s"
                        "" % self._name)
            server_action = ir_actions_server_obj.search(cr, SUPERUSER_ID,
                                                         [('name', '=', server_action_name),
                                                          ('model_id', '=', model_id),
                                                          ('state', '=', 'code')])

            # SERVER ACTION
            if server_action:
                assert len(server_action) <= 1, "More than one server action found!"
                logger.info("base.sosync init: server action exists")
                server_action_id = server_action[0]
                # Delete server action for recreation
                # logger.info("base.sosync init: Deleting server action %s for recreation!" % server_action)
                # ir_actions_server_obj.unlink(cr, SUPERUSER_ID, server_action)
                # server_action = False
            else:
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

            # 'MORE' MENU ENTRY
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
        # Appends the Z at the end to make it clear it is UTC
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

        # Get tracked fields
        tracked_fields = self._get_sosync_tracked_fields()
        if not tracked_fields:
            return dict()

        # Get watched_fields and val data
        watched_fields = dict()
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

    # TODO: set raise_ids_check to True after testing
    @api.multi
    def sosync_check(self, values=None, raise_ids_check=False):
        """ Check for for a new sosync version

        :param values: odoo field values (dict)
        :param raise_ids_check: if True raise an exception if the ids in no_sosync_jobs do not match ids in self
        :return: sosync_write_date, watched fields
        """
        if not values:
            values = dict()

        # SKIPP BY SOSYNCER FIELDS IN VALUES
        # ATTENTION: All computed fields (either by ORM on in create() write()) must be done in a separate call to
        #            create() or write() or the sosyncer fields in the vals will suppress the creation of sync jobs!!!
        skipp = False
        sosyncer_fields = self._sosyncer_fields
        if any(f in values for f in sosyncer_fields):
            skipp = True

        # If we only update the 'sosync_synced_version' field no other changes should happen to the record(s) of this
        # model! Therefore no sync jobs should be created! The syncer marks such updates by including
        # {'sosync_synced_version_update_only': {'res.partner': [1]}} in the context

        # Skipp any sync job creation for syncer writes where only the 'sosync_synced_version' is updated
        context = self.env.context if self.env and self.env.context else {}
        sosync_synced_version_update_only = context.get('sosync_synced_version_update_only', {})
        if self._name in sosync_synced_version_update_only:
            logger.info('Skipp sync job creation for sosync_synced_version_update: %s, %s' % (self._name, self.ids))
            skipp = True

        # DISABLED: Leads to unwanted side effects for computed fields or fields computed in create() or write() for
        #           the same model!
        # SKIPP BY SWITCH 'no_sosync_jobs' IN CONTEXT
        # elif self.env and self.env.context and 'no_sosync_jobs' in self.env.context:
        #     current_model = self._name
        #     no_sosync_jobs = self.env.context.get('no_sosync_jobs')
        #     if current_model in no_sosync_jobs:
        #
        #         # Check the record ids in no_sosync_jobs for the current model if any
        #         skipp_record_ids = no_sosync_jobs.get(current_model)
        #         if skipp_record_ids:
        #             unexpected_ids = set(skipp_record_ids).symmetric_difference(set(self.ids))
        #             if unexpected_ids:
        #                 msg = "Missing or unexpected ids in no_sosync_jobs! " \
        #                       "self._name: '%s', self.ids: '%s', no_sosync_jobs: '%s', unexpected_ids: '%s', " \
        #                       "values: '%s'" % (self._name, self.ids, no_sosync_jobs, unexpected_ids, values)
        #                 if raise_ids_check:
        #                     raise ValueError(msg)
        #                 else:
        #                     logger.error(msg)
        #
        #         # Set skipp to True
        #         skipp = True

        # CHECK FOR WATCHED FIELDS !!! IF NOT SKIPPED ALREADY !!!
        watched_fields = False
        if not skipp:
            watched_fields = self._sosync_watched_fields(values)

        # Return 'sosync write date' and 'watched fields' if not skipped and watched fields where found
        if watched_fields:
            return self._sosync_write_date_now(), watched_fields
        else:
            return False, False

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
        for record in self.sudo():
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

            # Append the new sync job queue record to the job_queue record set
            if job:
                job_queue = job_queue | job

        # Return the created sync jobs
        return job_queue

    @api.multi
    def create_sync_job_manually(self):
        """
        Manually create regular (job_source_type=False) sync jobs!
        HINT: This will only work if the record has already a sosync_write_date!
        :return:
        """
        job_queue = self.env["sosync.job.queue"].sudo()
        for record in self:
            if record.sosync_write_date:
                job = record.create_sync_job(job_date=record.sosync_write_date,
                                             job_source_type=False,
                                             job_source_fields='Manually created!')
                if job:
                    job_queue = job_queue | job

        return job_queue

    # -------------
    # CRUD AND COPY
    # -------------

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ATTENTION !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Odoo sorts abstract models always at the bottom of the python MRO (.__class__.__mro__). So this methods will not
    # be called first no matter what the addon dependency graph says.

    # The sosyncer will send the record_ids and model information in the context!
    # 'no_sosync_jobs'={model_name: [record_ids]}
    # e.g.: 'context': {'no_sosync_jobs': {'frst.personemailgruppe': [peg_id]}}

    # CREATE
    # ------
    @api.model
    def create(self, values, **kwargs):
        values = values if values else dict()

        # Detect sosync-record-version changes
        create_values = values
        sosync_write_date, watched_fields = self.sosync_check(values=values)
        if sosync_write_date:
            # When adding the sosync_write_date, clone the dictionary
            # first, otherwise all subsequently created models will
            create_values = dict(values)
            create_values['sosync_write_date'] = sosync_write_date

        # Create the record
        new_record = super(BaseSosync, self).create(create_values, **kwargs)

        # Create the sosync sync job
        if new_record and sosync_write_date:
            new_record.create_sync_job(sosync_write_date=sosync_write_date,
                                       job_source_fields=watched_fields)

        return new_record

    # WRITE
    # -----
    def _write(self, cr, user, ids, vals, context=None):
        """
            ATTENTION: _write() was used in addition to write to catch stored-computed-field changes!

            Computed fields that will be stored in the database will be recomputed by models.py > recompute() which
            will call _write(). If we inherit _write instead of write we may be able to check all relevant fields?

            # TODO: Further testing!
        """
        vals = vals if vals else dict()

        # Detect sosync-record-version changes
        sosync_write_date, watched_fields = self.sosync_check(cr, user, ids, values=vals, raise_ids_check=False,
                                                              context=context)
        if sosync_write_date:
            vals['sosync_write_date'] = sosync_write_date

        # Update the record(s)
        res = super(BaseSosync, self)._write(cr, user, ids, vals, context=context)

        # Create the sosync sync job(s)
        if res and sosync_write_date:
            recs = self.browse(cr, user, ids, context)
            recs.create_sync_job(sosync_write_date=sosync_write_date,
                                 job_source_fields=watched_fields)

        return res

    @api.multi
    def write(self, values, **kwargs):
        values = values if values else dict()

        # Detect sosync-record-version changes
        sosync_write_date, watched_fields = self.sosync_check(values=values)
        if sosync_write_date:
            values['sosync_write_date'] = sosync_write_date

        # Update the record(s)
        boolean_result = super(BaseSosync, self).write(values, **kwargs)

        # Create the sosync sync job(s)
        if boolean_result and sosync_write_date:
            self.create_sync_job(sosync_write_date=sosync_write_date,
                                 job_source_fields=watched_fields)

        return boolean_result

    # UNLINK
    # ------
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

        # Check for record-ids-to-skipp-sync-job in context
        no_sync_job_rec_ids = []
        if self.env and self.env.context and 'no_sosync_jobs' in self.env.context:
            no_sosync_jobs = self.env.context.get('no_sosync_jobs')
            no_sync_job_rec_ids = no_sosync_jobs.get(self._name, [])
        create_sync_job_records = self.filtered(lambda r: r.id not in no_sync_job_rec_ids)

        # Create sync jobs
        if create_sync_job_records:
            now = self._sosync_write_date_now()
            create_sync_job_records._create_comodel_delete_sync_jobs(sosync_write_date=now)
            create_sync_job_records.create_sync_job(sosync_write_date=now, job_source_type="delete")

        # Continue with the unlink method
        return super(BaseSosync, self).unlink()

    # COPY
    # ----
    # Remove sosync fields from data when a record is duplicated (copied) see copy_data() in models.py
    def copy_data(self, cr, uid, id, default=None, context=None):

        data_to_copy = super(BaseSosync, self).copy_data(cr, uid, id, default, context=context)

        # Remove sosync fields from data_to_copy
        for sosync_field in self._sosyncer_fields:
            data_to_copy.pop(sosync_field, None)

        return data_to_copy
