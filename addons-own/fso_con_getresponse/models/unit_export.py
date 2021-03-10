# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier, Michael Karrer
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
Export data to GetResponse.

An export will be forced if changes in both system are detected. (Concurrent write)
"""
import psycopg2
from psycopg2 import errorcodes
from contextlib import contextmanager
import json
from datetime import datetime
from datetime import timedelta
import pytz

from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.exception import IDMissingInBackend, RetryableJobError
from openerp.addons.connector.queue.job import job, related_action

from .helper_connector import get_environment, cmp_payloads
from .helper_related_action import unwrap_binding

import logging
_logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# SEARCH FOR ODOO RECORDS AND START THE EXPORT FOR EACH RECORD DELAYED OR DIRECT
# ------------------------------------------------------------------------------
# HINT: Only use the @getresponse decorator on the class where you define _model_name but not on the parent classes!
class BatchExporter(Exporter):
    """ The role of a BatchExporter is to search for a list of items to export, then it can either import them directly
    or delay (by connector job) the import of each item separately.
    """
    _model_name = None

    def run(self):
        raise NotImplementedError("The BatchExporter class uses batch_run() instead of run() to avoid confusion with "
                                  "the .run() method of the single record export class GetResponseExporter()!")

    def prepare_binding_records(self, unbound_unwrapped_records=None, domain=None, append_vals=None,
                                connector_no_export=None, limit=None):
        return self.binder.prepare_bindings(unbound_unwrapped_records=unbound_unwrapped_records, domain=domain,
                                            append_vals=append_vals, connector_no_export=connector_no_export,
                                            limit=limit)

    def get_binding_records(self, domain=None, limit=None):
        return self.binder.get_bindings(domain=domain, limit=limit)

    def _batch_export_records(self, binding_records, delay=None, fields=None, **kwargs):
        binding_model_name = self.model._name
        for record in binding_records:
            _logger.info("BATCH EXPORT: Export binding '%s', '%s', delay: %s"
                         "" % (binding_model_name, record.id, delay))
            if delay:
                export_record.delay(self.session,
                                    binding_model_name,
                                    record.id,
                                    fields=fields,
                                    **kwargs)
            else:
                export_record(self.session,
                              binding_model_name,
                              record.id,
                              fields=fields)

    # ATTENTION: The singe record exporter class GetResponseExporter and the batch exporter class BatchExporter
    #            both use .run to start the export (which is confusing at best).
    def batch_run(self, domain=None, fields=None, delay=False, batch=1000, **kwargs):
        """ Batch export odoo records to GetResponse

        :param batch: batch size
        :param delay: If True schedule a connector job if False export directly
        :param domain: odoo search domain for the binding records
        :type domain: list

        :param fields: list of odoo field names to export
        :type fields: list
        """
        _logger.info("BATCH EXPORT: START OF GETRESPONSE BATCH EXPORT! model: %s, domain: %s, delay: %s"
                     "" % (self.model._name, domain, delay))

        # ----------------------------
        # EXPORT NEW PREPARED BINDINGS
        # ----------------------------
        all_exported_binding_ids = []
        prepared_bindings = True
        while prepared_bindings:
            # PREPARE MISSING BINDINGS
            # ATTENTION: Prevent the potential export of the bindings by consumers with connector_no_export=True!
            prepared_bindings = self.prepare_binding_records(connector_no_export=True, limit=batch)

            _logger.info("BATCH EXPORT: Prepared %s bindings to batch export! ('%s', '%s')"
                         "" % (len(prepared_bindings), prepared_bindings._name, prepared_bindings.ids))

            # EXPORT THE PREPARED BINDINGS (or create connector jobs depending on delay)
            self._batch_export_records(prepared_bindings, delay=delay, fields=fields, **kwargs)
            all_exported_binding_ids += prepared_bindings.ids

            # FORCE COMMIT TO STORE THE BINDINGS AND CONNECTOR JOBS TO IMMEDIATELY START THE EXPORT
            self.session.commit()

        # ------------------------
        # EXPORT EXISTING BINDINGS
        # ------------------------
        domain = [] if not domain else domain
        binding_records = True
        while binding_records:
            # SEARCH FOR EXISTING BINDING RECORDS
            remaining_domain = domain + [('id', 'not in', all_exported_binding_ids)]
            binding_records = self.get_binding_records(domain=remaining_domain, limit=batch)
            _logger.info("BATCH EXPORT: Found %s bindings to batch export for remaining_domain '%s'! ('%s', '%s')"
                         "" % (len(binding_records), remaining_domain, binding_records._name, binding_records.ids))

            # EXPORT THE BINDINGS (or create connector jobs depending on delay)
            self._batch_export_records(binding_records, delay=delay, fields=fields, **kwargs)
            all_exported_binding_ids += binding_records.ids

            # FORCE COMMIT TO STORE THE CONNECTOR JOBS TO IMMEDIATELY START THE EXPORT
            self.session.commit()


# ------------------------------------
# EXPORT AN ODOO RECORD TO GETRESPONSE
# ------------------------------------
# HINT: Only use the @getresponse decorator on the class where you define _model_name but not on the parent classes!
class GetResponseExporter(Exporter):
    """ A common flow for the exports to GetResponse """
    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(GetResponseExporter, self).__init__(connector_env)
        self.binding_id = None
        self.getresponse_id = None
        self.binding_record = None

        # Getresponse record returned from the getresponse-python lib
        self.getresponse_record = None

    def _get_binding_record(self):
        """ Return the binding record """
        binding = self.binder.get_bindings(domain=[('id', '=', self.binding_id)])
        assert len(binding) <= 1, "More than one binding record returned!"
        if binding:
            assert binding.id == self.binding_id, "Id of returned binding does not match self.binding_id!"
            assert binding._name == self.model._name, "Model of binding record does not match self.model"
        return binding

    def _lock(self):
        """ Lock the binding record.

        Lock the binding record so we are sure that only one export job is running for this record if concurrent jobs
        have to export the same record.

        When concurrent jobs try to export the same record, the first one will lock and proceed, the others will fail
        to lock and will be retried later.

        ATTENTION: This behavior works also when the export becomes multilevel!
        with :meth:`_export_dependencies`. Each level will set its own lock on the binding record it has to export.

        """
        sql = ("SELECT id FROM %s WHERE ID = %%s FOR UPDATE NOWAIT" %
               self.model._table)
        try:
            self.session.cr.execute(sql, (self.binding_id, ),
                                    log_exceptions=False)
        except psycopg2.OperationalError:
            _logger.info('A concurrent job is already exporting the same '
                         'record (%s with id %s). Job delayed later.',
                         self.model._name, self.binding_id)
            raise RetryableJobError(
                'A concurrent job is already exporting the same record '
                '(%s with id %s). The job will be retried later.' %
                (self.model._name, self.binding_id))

    def _still_exists_in_getresponse(self):
        if self.getresponse_id:
            self.backend_adapter.read(self.getresponse_id)

    def _skip_export_for_updates(self):
        """ Return a message if the export must be skipped because e.g.:
              - odoo data has not changed since last sync
            or raise an exception to prevent the export e.g.:
              - no changes in odoo but write date in GetResponse is newer than the sync_date in odoo

              Returns: a message if the export must be skipped or 'False' to continue with the export
        """
        # Skip checks for unbound records or records with prepared bindings because these would create new records
        binding = self.binding_record
        if not binding or not binding.getresponse_id:
            return False

        # GetResponse update-payload-data of the last sync
        last_sync_cmp_data = json.loads(binding.compare_data, encoding='utf8') if binding.compare_data else {}

        # Current odoo record export update data (=GetResponse update payload)
        # ATTENTION: The export mapper would merge the current getresponse data with the current odoo data!
        #            !!! Therefore we need to set no_external_data=True !!!
        map_record = self.mapper.map_record(binding)
        current_odoo_export_data = map_record.values(no_external_data=True)

        # SKIPP EXPORT BECAUSE NO CHANGES WHERE MADE IN ODOO SINCE LAST EXPORT
        if cmp_payloads(last_sync_cmp_data, current_odoo_export_data) == 0:
            msg = ("SKIPP export of '%s'! Export data did not change since last export for binding '%s', '%s'!"
                   "\n\ncurrent_odoo_export_data:\n%s,\n\nlast_sync_cmp_data:\n%s"
                   "" % (self.getresponse_id, binding._name, binding.id, current_odoo_export_data, last_sync_cmp_data))
            _logger.info(msg)
            # Skip the export by returning a message
            return msg

        # CHECK FOR CHANGES IN GETRESPONSE SINCE THE LAST IMPORT
        # HINT: Right now this check will only trigger a log message and nothing else! The export will be done and may
        #       override GetResponse data! This is less of a problem because the export mapper for contacts will
        #       merge the current getresponse tags and custom fields - so no or very little data could be lost.
        if binding.sync_date:
            last_sync_date = datetime.strptime(binding.sync_date, DEFAULT_SERVER_DATETIME_FORMAT)
            try:
                getresponse_record = self.backend_adapter.read(self.getresponse_id)
            except IDMissingInBackend:
                raise IDMissingInBackend('GetResponse ID %s no longer exits!' % self.getresponse_id)
            except Exception as e:
                raise e
            getresponse_create_date = getresponse_record.get('created_on', None)
            getresponse_write_date = getresponse_record.get('changed_on', None)
            gr_last_change = getresponse_write_date or getresponse_create_date
            if gr_last_change:
                if gr_last_change.tzinfo is None or gr_last_change.tzinfo.utcoffset(gr_last_change) is None:
                    gr_last_change = pytz.utc.localize(gr_last_change)
                if last_sync_date.tzinfo is None or last_sync_date.tzinfo.utcoffset(last_sync_date) is None:
                    last_sync_date = pytz.utc.localize(last_sync_date)
                difference = gr_last_change - last_sync_date
                # If the last change in getresponse was 5 or more second later then the last sync we log a message
                if difference.total_seconds() >= 5:
                    msg = ("FORCE EXPORT of '%s' because data changed in both systems for binding '%s', '%s'!"
                           " GetResponse data will be overwritten! gr_last_change: %s, last_sync_date: %s"
                           "" % (self.getresponse_id, binding._name, binding.id, gr_last_change, last_sync_date))
                    # Do NOT skip the export but log an error message
                    _logger.error(msg)

        # Continue with the export
        return False

    @contextmanager
    def _retry_unique_violation(self):
        """ Context manager: catch Unique constraint error and retry the job later.

        When we execute several jobs workers concurrently, it happens that 2 jobs are creating the same record at the
        same time (binding record created by :meth:`_export_dependency`), resulting in:

            IntegrityError: duplicate key value violates unique constraint "getresponse_uniq"
            DETAIL:  Key (backend_id, openerp_id)=(1, 4851) already exists.

        In that case, we'll retry the import just later.

        .. warning:: The unique constraint must be created on the binding record to prevent 2 bindings to be created
                     for the same GetResponse record!
        """
        try:
            yield
        except psycopg2.IntegrityError as err:
            if err.pgcode == psycopg2.errorcodes.UNIQUE_VIOLATION:
                raise RetryableJobError(
                    'A database error caused the failure of the job:\n'
                    '%s\n\n'
                    'Likely due to 2 concurrent jobs wanting to create '
                    'the same record. The job will be retried later.' % err)
            else:
                raise

    def _export_dependency(self, related_record, exporter_class=None, prepared_binding_extra_vals=None):
        """
        Export a dependency. The exporter class is a subclass of ``GetResponseExporter``. If a more precise class
        needs to be defined, it can be passed to the ``exporter_class`` keyword argument.

        .. warning:: a commit is done at the end of the export of each dependency. The reason for that is that we
                     pushed a record on the backend and we absolutely have to keep its ID.

                     So you *must* take care not to modify the OpenERP database during an export, excepted when writing
                     back the external ID or eventually to store external data that we have to keep on this side.

                     You should call this method only at the beginning of the exporter synchronization,
                     in :meth:`~._export_dependencies`.

        :param related_record: record to export if not already exported may be a binding or an unwrapped record
        :type related_record: :py:class:`openerp.models.BaseModel`
        :param exporter_class: :py:class:`openerp.addons.connector.connector.ConnectorUnit` class or parent class to use
                             for the export.
                             By default: GetResponseExporter
        :type exporter_class: :py:class:`openerp.addons.connector.connector.MetaConnectorUnit`
        :prepared_binding_extra_vals:  In case we want to prepare a new binding pass extra values for this binding
        :type prepared_binding_extra_vals: dict
        """
        # HINT: The binder field names must be the same for all getresponse related binding models!
        assert related_record.ensure_one(), "related_record must be a single odoo record!"
        binding_ids_field = self.binder._inverse_binding_ids_field
        backend_field = self.binder._backend_field

        # 'related_record' is an unwrapped record
        if hasattr(related_record, binding_ids_field):
            unwrapped_record = related_record

            # Search for an existing binding for the current backend
            existing_bindings = getattr(unwrapped_record, binding_ids_field)
            binding = existing_bindings.filtered(lambda r: getattr(r, backend_field).id == self.backend_record.id)

            # Get the binding model and the correct binder for the binding model
            binding_model = existing_bindings._name
            binder = self.binder_for(binding_model)

        # 'related_record' is a binding record
        else:
            binding = related_record

            # Get the binding model and the correct binder for the binding model
            binding_model = binding._name
            binder = self.binder_for(binding_model)

            # Get the unwrapped record for this binding
            unwrapped_record = binder.unwrap_binding(binding.id, browse=True)

        assert len(unwrapped_record) == 1, "None or more than one unwrapped records found! %s" % unwrapped_record

        # Prepare a binding record for the export
        if not binding:
            # If jobs create the binding at the same time, retry later.
            # WARNING: A unique constraint (backend_id, openerp_id) MUST exist on the binding model!
            with self._retry_unique_violation():
                binding = binder.prepare_bindings(domain=[('id', '=', unwrapped_record.id)],
                                                  append_vals=prepared_binding_extra_vals,
                                                  connector_no_export=True)
                # Eager commit to avoid having 2 jobs exporting at the same time. The constraint will pop if an
                # other job already created the same binding. It will be caught and raise a RetryableJobError.
                self.session.commit()

        assert len(binding) == 1, "None or more than one binding records found! %s" % binding

        # Export the binding if it is a prepared binding (no external id)
        external_id = binder.to_backend(binding)
        if not external_id:
            # Get the exporter
            if exporter_class is None:
                exporter_class = GetResponseExporter
            # Create a new connector environment and exporter for the binding model
            exporter = self.unit_for(exporter_class, model=binding_model)

            # Run the export
            _logger.info("Export dependency binding '%s', '%s'" % (binding._name, binding.id))
            exporter.run(binding.id)

        else:
            _logger.info("Export dependency SKIPPED because binding with an external id exists: '%s', '%s'"
                         "" % (binding._name, binding.id))

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        return

    def _get_map_record(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`
        """
        return self.mapper.map_record(self.binding_record)

    def _validate_create_data(self, data):
        """ Check if the values to export are correct

        Pro-actively check before the ``Model.create`` if some fields are missing or invalid

        Raise `InvalidDataError`
        """
        return

    def _validate_update_data(self, data):
        """ Check if the values to export are correct

        Pro-actively check before the ``Model.update`` if some fields are missing or invalid

        Raise `InvalidDataError`
        """
        return

    def _create_data(self, map_record, fields=None, **kwargs):
        """ Get the data to pass to :py:meth:`_create` """
        return map_record.values(for_create=True, fields=fields, **kwargs)

    def create(self, create_data=None):
        if not create_data:
            return _('Nothing to export.')

        # ADD THE RETURNED GETRESPONSE_RECORD TO SELF
        self.getresponse_record = self.backend_adapter.create(create_data)

        # Store the getresponse id (external id) to use it in _update_binding_after_export()
        assert self.getresponse_record.id, "GetResponse Object did not return an id! %s" % self.getresponse_record
        self.getresponse_id = self.getresponse_record.id

        # Log the export
        _logger.info("EXPORT: '%s' created in GetResponse as '%s' with create data '%s'"
                     "" % (self.model._name, self.getresponse_id, create_data))

    def _update_data(self, map_record, fields=None, **kwargs):
        """ Get the data to pass to :py:meth:`_update` """
        return map_record.values(fields=fields, **kwargs)

    def update(self, update_data=None):
        if not update_data:
            return _('Nothing to export.')

        assert self.getresponse_id

        # Store the returned getresponse_record
        self.getresponse_record = self.backend_adapter.write(self.getresponse_id, update_data)

        # Compare the returned getresponse_id with the initial getresponse id
        assert self.getresponse_id == self.getresponse_record.id, _(
            "Binding GetResponse id '%s' does not match GetRepsonse ID '%s' of the returned object!!"
            "" % (self.getresponse_id, self.getresponse_record.id)
        )

        # Log the export
        _logger.info("EXPORT: Data for binding '%s', '%s' exported to GetResponse '%s'"
                     "" % (self.binding_record._name, self.binding_record.id, self.getresponse_id))

    def _update_binding_after_export(self, map_record, sync_data=None, compare_data=None):
        """ Bind the record again after the export to update bind record data! (sync date, external id ...) """
        self.binder.bind(self.getresponse_id, self.binding_id,
                         sync_data=sync_data, compare_data=compare_data)

    def skipp_after_export_methods(self):
        return False

    def _check_data_in_gr_after_export(self, *args, **kwargs):
        return

    def _export_related_bindings(self, *args, **kwargs):
        return

    def _after_export(self, *args, **kwargs):
        """ Can do several actions after exporting a record to GetResponse """
        return

    # ------------------------------------------
    # EXPORT THE RECORD FROM ODOO TO GETRESPONSE
    # ------------------------------------------
    def run(self, binding_id, *args, **kwargs):
        """ Run the synchronization

        :param binding_id: identifier of the binding record to export
        """
        _logger.info("EXPORT: run() for binding %s, %s" % (self.model._name, binding_id))
        # DISABLED: Because it makes everything much harder to compare!
        # Get the fields list to export from the kwargs (this will limit the exported fields for the update)
        # if self.getresponse_id:
        #     fields = kwargs.get('fields', None)
        # else:
        #     # Do not limit the fields if a new record will be created in GetResponse
        #     fields = None
        if kwargs.get('fields', False):
            _logger.error("EXPORT: fields in kwargs! Reset fields to Null!")
            kwargs['fields'] = None

        self.binding_id = binding_id

        # SKIP BY BINDING
        # ---------------
        # Get the binding
        self.binding_record = self._get_binding_record()
        if not self.binding_record:
            msg = _("Export of '%s', '%s' was SKIPPED BY BINDING! The binding no longer exists or was filtered"
                    " out by binder.get_bindings()!") % (self.model._name, binding_id)
            _logger.warning(msg)
            return msg

        # Get the GetResponse ID of the record (if it is already bound/synced)
        self.getresponse_id = self.binder.to_backend(self.binding_id)

        # CHECK IF THE RECORD STILL EXISTS IN GETRESPONSE
        # -----------------------------------------------
        # HINT: This should raise an IDMissingInBackend exception if the record was removed!
        self._still_exists_in_getresponse()

        # SKIP EXPORT FOR UPDATES
        # -----------------------
        # E.g. if the odoo data did not change since the last export
        skip_export = self._skip_export_for_updates()
        if skip_export:
            return skip_export

        # -------------------
        # EXPORT DEPENDENCIES
        # -------------------
        self._export_dependencies()

        # Prevent other jobs to export the same record. Will be released on commit (or rollback)
        self._lock()

        # Get the connector map record (for the export this is the odoo record)
        map_record = self._get_map_record()

        # ---------------------------
        # UPDATE A GETRESPONSE RECORD
        # ---------------------------
        # Get the update data for GetResponse
        payload_create_data = None
        payload_update_data = self._update_data(map_record, fields=None)
        if self.getresponse_id:
            # Check the update data before export
            self._validate_update_data(payload_update_data)
            # Update the record in GetResponse and store the the returned getresponse record data in self
            self.update(update_data=payload_update_data)

        # ---------------------------
        # CREATE A GETRESPONSE RECORD
        # ---------------------------
        else:
            # Get the create data for GetResponse
            payload_create_data = self._create_data(map_record, fields=None)
            # Check the create data before export
            self._validate_create_data(payload_create_data)
            # Create the record in getresponse and store the returned getresponse record and id in self
            self.create(create_data=payload_create_data)

        # --------------------------------------
        # UPDATE THE BINDING RECORD AFTER EXPORT
        # --------------------------------------
        sync_data = payload_create_data if payload_create_data else payload_update_data
        self._update_binding_after_export(map_record, sync_data=sync_data, compare_data=payload_update_data)

        # COMMIT SO WE KEEP THE EXTERNAL ID WHEN THERE ARE SEVERAL EXPORTS (DUE TO DEPENDENCIES) AND ONE OF THEM FAILS.
        # The commit will also release the lock acquired on the binding record
        self.session.commit()

        # ------------------------------
        # SKIPP ALL AFTER EXPORT METHODS
        # ------------------------------
        skipp_after_export_methods = self.skipp_after_export_methods()
        if skipp_after_export_methods:
            return _("Binding '%s', '%s' was exported to GetResponse '%s' without after export methods."
                     ) % (self.binding_record._name, self.binding_record.id, self.getresponse_id)

        # CHECK DATA IN GETRESPONSE AFTER THE EXPORT
        # ------------------------------------------
        self._check_data_in_gr_after_export(*args, **kwargs)

        # EXPORT RELATED BINDINGS AFTER AN EXPORT
        # ---------------------------------------
        if 'skip_export_related_bindings' not in kwargs:
            self._export_related_bindings(*args, **kwargs)

        # DO STUFF AFTER A RECORD EXPORT
        # ------------------------------
        if 'skip_after_export' not in kwargs:
            self._after_export(*args, **kwargs)

        # Return the _run() result
        _logger.info("EXPORT: run() for binding %s, %s DONE!" % (self.model._name, binding_id))
        return _("Binding '%s', '%s' was exported to GetResponse '%s'."
                 ) % (self.binding_record._name, self.binding_record.id, self.getresponse_id)


# HINT: The @related_action decorator will add a button on the jobs form view that will open the form view of the
#       unwrapped record. E.g. a job for getresponse.frst.zgruppedetail will open the form view for frst.zgruppedetail
# ATTENTION: export_record expects binding records !!! Create them first if needed!
#            Check CampaignBatchExporter batch_run() for an example!
@job(default_channel='root.getresponse', retry_pattern={1: 60, 2: 60 * 2, 3: 60 * 10, 5: 60*60})
@related_action(action=unwrap_binding)
def export_record(session, model_name, binding_id, fields=None):
    """ Export an odoo record to GetResponse """
    _logger.info("EXPORT: export_record() for binding %s, %s" % (model_name, binding_id))
    # Get the odoo binding record
    record = session.env[model_name].browse(binding_id)

    # Get an connector environment
    env = get_environment(session, model_name, record.backend_id.id)

    # ATTENTION: The GetResponseExporter class may be changed by the model specific implementation!
    #            The connector knows which classes to consider based on the _model_name of the class and the
    #            'model_name' in the args of import_record used in the connector environment above
    exporter = env.get_connector_unit(GetResponseExporter)

    # Start the .run() method of the found exporter class
    # ATTENTION: The binding is checked/validate in .run() by _get_binding_record() > binder.get_bindings()
    return exporter.run(binding_id, fields=fields)
