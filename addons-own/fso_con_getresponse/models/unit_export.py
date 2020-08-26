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

from openerp.tools.translate import _

from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.exception import IDMissingInBackend, RetryableJobError
from openerp.addons.connector.queue.job import job, related_action

from .unit_import import import_record
from .helper_connector import get_environment
from .helper_related_action import unwrap_binding
from .unit_binder import GetResponseBinder

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
        raise ValueError("The BatchExporter class uses batch_run() instead of run() to avoid confusion with the .run()"
                         " method of the single record export class GetResponseExporter()!")

    def prepare_binding_records(self):
        return self.binder.prepare_bindings()

    def get_binding_records(self, domain=None):
        return self.binder.get_bindings(domain=domain)

    # ATTENTION: The singe record exporter class GetResponseExporter and the batch exporter class BatchExporter
    #            both use .run to start the export (which is confusing at best).
    def batch_run(self, domain=None, fields=None, delay=False, **kwargs):
        """ Batch export odoo records to GetResponse

        :param domain: odoo search domain for the binding records
        :type domain: list

        :param fields: list of odoo field names to export
        :type fields: list
        """

        # -------------------------------------
        # PREPARE BINDING RECORDS BEFORE SEARCH
        # -------------------------------------
        prepared_bindings = self.prepare_binding_records()
        _logger.info("Prepared %s bindings before batch export! ('%s', '%s')"
                     "" % (len(prepared_bindings), prepared_bindings._name, prepared_bindings.ids))

        # --------------------------
        # SEARCH FOR BINDING RECORDS
        # --------------------------
        binding_records = self.get_binding_records(domain=domain)
        _logger.info("Found %s bindings to batch export! ('%s', '%s')"
                     "" % (len(binding_records), binding_records._name, binding_records.ids))

        # -------------------------------------------------
        # RUN export_record() FOR EACH FOUND BINDING RECORD
        # -------------------------------------------------
        binding_model_name = self.model._name
        for record in binding_records:
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

    def _delay_import(self):
        """ Schedule an import of the record.

        Adapt in the sub-classes when the model is not imported using ``import_record``.
        """
        # 'force' is 'True' because the sync_date will be more recent so the import would be skipped
        assert self.getresponse_id
        import_record.delay(self.session, self.model._name, self.backend_record.id, self.getresponse_id, force=True)

    # TODO
    def _should_import(self):
        """ Before the export, compare the update date (todo: and data) in GetResponse and the last sync date (todo: and data) in Odoo,
        if the update date in GetResponse is more recent (todo: and there where no changes in odoo),
        schedule an import to not miss changes done in GetResponse.

        TODO: If changes in both system happened _should_import() will return False to enforce the export! This means
              the data in odoo wins in case of changes in both systems
        """
        assert self.binding_record

        # Record was never synced (export new-odoo-record)
        if not self.getresponse_id:
            return False

        # If a binding record exists already we first check if the record was already exported. If it was already
        # exported it will have a sync_date if the export was not done yet we need to trigger the export.
        sync_date_string = self.binding_record.sync_date
        if not sync_date_string:
            return True

        # Read the getresponse record data
        getresponse_record = self.backend_adapter.read(self.getresponse_id)

        # TODO: At this point we should import the GetResponse record first if:
        #           - the odoo record has NO! changes (binding_record.sync_data == odoo record data)
        #           and
        #           - the getresponse_record has changed (binding_record.sync_data != getresponse_record data)

        # HINT: TODO: For the prototype we will just start the export - replace with the result of the check above when
        #             finished
        return False

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

    def _has_to_skip(self):
        """ Return True if the export can be skipped """
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

    # TODO: Check where the field 'magento_bind_ids' is used in the original magento connector addon to know how and
    #       where to use getresponse_bind_ids
    def _export_dependency(self, relation, binding_model, exporter_class=None,
                           binding_field='getresponse_bind_ids', binding_extra_vals=None):
        """
        Export a dependency. The exporter class is a subclass of ``GetResponseExporter``. If a more precise class
        needs to be defined, it can be passed to the ``exporter_class`` keyword argument.

        .. warning:: a commit is done at the end of the export of each dependency. The reason for that is that we
                     pushed a record on the backend and we absolutely have to keep its ID.

                     So you *must* take care not to modify the OpenERP database during an export, excepted when writing
                     back the external ID or eventually to store external data that we have to keep on this side.

                     You should call this method only at the beginning of the exporter synchronization,
                     in :meth:`~._export_dependencies`.

        :param relation: record to export if not already exported
        :type relation: :py:class:`openerp.models.BaseModel`
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param exporter_cls: :py:class:`openerp.addons.connector.connector.ConnectorUnit` class or parent class to use
                             for the export.
                             By default: GetResponseExporter
        :type exporter_cls: :py:class:`openerp.addons.connector.connector.MetaConnectorUnit`
        :param binding_field: name of the one2many field on a normal record that points to the binding record
                              (default: magento_bind_ids).
                              It is used only when the relation is not a binding but is a normal record.
        :type binding_field: str | unicode
        :binding_extra_vals:  In case we want to create a new binding pass extra values for this binding
        :type binding_extra_vals: dict
        """
        if not relation:
            return
        if exporter_class is None:
            exporter_class = GetResponseExporter

        # Get an instance of the binder class for the current model
        rel_binder = self.binder_for(binding_model)

        # Use the field names of the binder
        # TODO: Check if this is correct for the domains and the dict below
        binder_openerp_field = rel_binder._openerp_field
        binder_backend_field = rel_binder._backend_field

        # 'wrap' is typically 'True' if the relation is for instance a 'product.product' record but the binding model is
        # 'magento.product.product'
        wrap = relation._model._name != binding_model

        if wrap and hasattr(relation, binding_field):
            # TODO: check if the correct field names of the binder are used!
            domain = [(binder_openerp_field, '=', relation.id),
                      (binder_backend_field, '=', self.backend_record.id)]
            binding = self.env[binding_model].search(domain)
            if binding:
                assert len(binding) == 1, 'Only 1 binding for a backend is supported in _export_dependency'
            # We are working with a unwrapped record (e.g. product.category) and the binding does not exist yet.
            # Example: I created a product.product and its binding magento.product.product and we are exporting it,
            # but we need to create the binding for the product.category on which it depends.
            else:
                # TODO: check if the correct field names of the binder are used!
                bind_values = {binder_backend_field: self.backend_record.id,
                               binder_openerp_field: relation.id}
                if binding_extra_vals:
                    bind_values.update(binding_extra_vals)
                # If 2 jobs create it at the same time, retry one later. A unique constraint (backend_id, openerp_id)
                # should exist on the binding model
                with self._retry_unique_violation():
                    binding = (self.env[binding_model]
                               .with_context(connector_no_export=True)
                               .sudo()
                               .create(bind_values))
                    # Eager commit to avoid having 2 jobs exporting at the same time. The constraint will pop if an
                    # other job already created the same binding. It will be caught and raise a RetryableJobError.
                    self.session.commit()
        else:
            # If magento_bind_ids does not exist we are typically in a
            # "direct" binding (the binding record is the same record).
            # If wrap is True, relation is already a binding record.
            binding = relation

        if not rel_binder.to_backend(binding):
            exporter = self.unit_for(exporter_class, model=binding_model)
            exporter.run(binding.id)

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        return

    def _map_data(self):
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

    def create(self, map_record, fields=None):
        create_data = self._create_data(map_record, fields=fields)
        if not create_data:
            return _('Nothing to export.')

        # Special check on data before export
        self._validate_create_data(create_data)

        # ADD THE RETURNED GETRESPONSE_RECORD TO SELF
        self.getresponse_record = self.backend_adapter.create(create_data)

        # UPDATE THE EXTERNAL ID FOR THE BINDING UPDATE LATER ON IN .run()
        assert self.getresponse_record.id, "GetResponse Object did not return an id! %s" % self.getresponse_record
        self.getresponse_id = self.getresponse_record.id

    def _update_data(self, map_record, fields=None, **kwargs):
        """ Get the data to pass to :py:meth:`_update` """
        return map_record.values(fields=fields, **kwargs)

    def update(self, map_record, fields=None):
        update_data = self._update_data(map_record, fields=fields)
        if not update_data:
            return _('Nothing to export.')

        assert self.getresponse_id

        # Special check on data before export
        self._validate_update_data(update_data)

        # Add the returned getresponse_record to self
        self.getresponse_record = self.backend_adapter.write(self.getresponse_id, update_data)

        # Check the returned getresponse_id
        assert self.getresponse_id == self.getresponse_record.id, _(
            "Binding GetResponse id '%s' does not match GetRepsonse ID '%s' of the returned object!!"
            "" % (self.getresponse_id, self.getresponse_record.id)
        )

    def _bind_after_export(self):
        """ Bind the record again after the export to update bind record data! (sync date, external id ...)"""
        map_record = self._map_data()
        update_values = self._update_data(map_record)
        self.binder.bind(self.getresponse_id, self.binding_id, sync_data=update_values)

    def _after_export(self):
        """ Can do several actions after exporting a record to GetResponse """
        pass

    def _run(self, fields=None):
        """ Flow of the synchronization. May be implemented in inherited classes"""
        assert self.binding_id
        assert self.binding_record

        if not self.getresponse_id:
            fields = None  # should be created with all the fields

        if self._has_to_skip():
            return

        # Export the missing linked resources first
        self._export_dependencies()

        # Prevent other jobs to export the same record. Will be released on commit (or rollback)
        self._lock()

        map_record = self._map_data()

        # ---------------------------
        # UPDATE A GETRESPONSE RECORD
        # ---------------------------
        if self.getresponse_id:
            self.update(map_record, fields=fields)

        # -------------------------------------------------------------------
        # CREATE A GETRESPONSE RECORD AND UPDATE THE 'getresponse_id' of self
        # -------------------------------------------------------------------
        else:
            self.create(map_record, fields=fields)

        return _('Record with ID %s was exported to GetResponse.') % self.getresponse_id

    # ------------------------------------------
    # EXPORT THE RECORD FROM ODOO TO GETRESPONSE
    # ------------------------------------------
    def run(self, binding_id, *args, **kwargs):
        """ Run the synchronization

        :param binding_id: identifier of the binding record to export
        """
        self.binding_id = binding_id

        # Get (and validate) the binding-model-record
        self.binding_record = self._get_binding_record()
        if not self.binding_record:
            return _('Export of binding (%s, %s) was SKIPPED by binder.get_bindings()!'
                     ) % (self.model._name, binding_id)

        # Get the GetResponse ID of the record (if it is already bound/synced)
        self.getresponse_id = self.binder.to_backend(self.binding_id)

        # CHECK IF WE NEED TO IMPORT THE RECORD FROM GETRESPONSE TO ODOO BEFORE WE EXPORT THE RECORD
        # Import the record prior to the export only if changes are detected in GetResponse but not in odoo!
        try:
            should_import = self._should_import()
        except IDMissingInBackend:
            self.getresponse_id = None
            should_import = False
        if should_import:
            self._delay_import()

        # RUN THE EXPORT
        # (synchronization flow of the bound model)
        result = self._run(*args, **kwargs)

        # BIND THE RECORD AFTER THE EXPORT TO UPDATE THE BINDING-RECORD DATA
        # (to update bind record data and add sync_data like in the importer)
        self._bind_after_export()

        # COMMIT SO WE KEEP THE EXTERNAL ID WHEN THERE ARE SEVERAL EXPORTS (DUE TO DEPENDENCIES) AND ONE OF THEM FAILS.
        # The commit will also release the lock acquired on the binding record
        self.session.commit()

        # HOOK TO DO STUFF AFTER A RECORD EXPORT
        # TODO: Update the odoo record with the data from the getresponse object stored in self.getresponse_record
        #       Check _run() to see where it is stored! I think this would best fit in _after_export()?!?
        #       !!! But be careful not to trigger an other export so update the context accordingly !!!
        self._after_export()

        # Return the _run() result
        return result


# HINT: The @related_action decorator will add a button on the jobs form view that will open the form view of the
#       unwrapped record. E.g. a job for getresponse.frst.zgruppedetail will open the form view for frst.zgruppedetail
# ATTENTION: export_record expects binding records !!! Create them first if needed!
#            Check ZgruppedetailBatchExporter batch_run() for an example!
@job(default_channel='root.getresponse')
@related_action(action=unwrap_binding)
def export_record(session, model_name, binding_id, fields=None):
    """ Export an odoo record to GetResponse """
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
