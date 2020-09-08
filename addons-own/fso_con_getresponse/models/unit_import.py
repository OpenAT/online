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
Import data from GetResponse.

An import can be skipped if changes in both system are detected. (Concurrent write)

ATTENTION: Call the ``bind`` method even if the records are already bound, to update the last sync date.

"""

import logging
from copy import deepcopy

from openerp.tools.translate import _

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.unit.mapper import ExportMapper
from openerp.addons.connector.exception import IDMissingInBackend

from .helper_connector import get_environment, cmp_payloads
from .unit_export import GetResponseExporter

import json

_logger = logging.getLogger(__name__)


# ----------------------------------------
# ADD A CHECKPOINT FOR MANUAL INTERVENTION
# ----------------------------------------
# TODO: Check where and how to add checkpoints in the sync process
# @getresponse
# class AddCheckpoint(ConnectorUnit):
#     """ Add a connector.checkpoint on the underlying model
#     (not the getresponse.* but the _inherits'ed model) """
#
#     _model_name = ['getresponse.frst.zgruppedetail']
#
#     def run(self, openerp_binding_id):
#         binding = self.model.browse(openerp_binding_id)
#         record = binding.openerp_id
#         add_checkpoint(self.session,
#                        record._model._name,
#                        record.id,
#                        self.backend_record.id)


# -------------------------------------------------------------------------
# SEARCH FOR RECORDS AND START THE IMPORT FOR EACH RECORD DELAYED OR DIRECT
# -------------------------------------------------------------------------
# HINT: Only use the @getresponse decorator on the class where you define _model_name but not on the parent classes!
class BatchImporter(Importer):
    """ The role of a BatchImporter is to search for a list of items to import, then it can either import them
    directly or delay the import of each item separately.
    """
    _model_name = None

    def run(self):
        raise ValueError("The BatchImporter class uses batch_run() instead of run() to avoid confusion with the .run()"
                         " method of the single record export class GetResponseImporter()!")

    def _batch_run_search(self, filters=None, **kwargs):
        return self.backend_adapter.search(filters)

    def batch_run(self, filters=None, delay=False, **kwargs):
        """ Run the synchronization """

        # ---------------------------------
        # SEARCH FOR GETRESPONSE RECORD IDS
        # ---------------------------------
        getresponse_record_ids = self._batch_run_search(filters=filters, **kwargs)

        # -----------------------------------------
        # RUN import_record() FOR EACH FOUND RECORD
        # -----------------------------------------
        for record_id in getresponse_record_ids:
            if delay:
                import_record.delay(self.session,
                                    self.model._name,
                                    self.backend_record.id,
                                    record_id,
                                    **kwargs)
            else:
                import_record(self.session,
                              self.model._name,
                              self.backend_record.id,
                              record_id)


# ---------------------------
# IMPORT A GETRESPONSE RECORD
# ---------------------------
# HINT: Only use the @getresponse decorator on the class where you define _model_name but not on the parent classes!
class GetResponseImporter(Importer):
    """ Base importer for GetResponse records """

    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(GetResponseImporter, self).__init__(connector_env)
        self.getresponse_id = None
        self.getresponse_record = None
        self.binding_record = None
        self.map_record = None

    def _get_getresponse_data(self):
        """ Return the raw Getresponse object/data for ``self.getresponse_id`` """
        return self.backend_adapter.read(self.getresponse_id)

    def _before_import(self):
        """ Hook called before the import, when we have the GetResponse data"""

    def _skip_import_for_updates(self):
        """ Return a message if the import must be skipped because e.g.:
              - concurrent write (odoo data has changed since last sync but was not exported)
        """
        # Make sure we already have the getresponse record data
        assert self.getresponse_record, "self.getresponse_record is missing"

        # Skipp import check for unbound records or records with prepared bindings because these would create new recs
        binding = self.binding_record
        if not binding or not binding.getresponse_id:
            return False

        # DETECT UNEXPORTED ODOO CHANGES SINCE THE LAST SYNC
        if binding.compare_data:
            last_sync_cmp_data = json.loads(binding.compare_data, encoding='utf8') if binding.compare_data else {}

            # Current odoo record export update data (=GetResponse update payload)
            # ATTENTION: The export mapper would merge the current getresponse data with the current odoo data!
            #            !!! Therefore we need to set no_external_data=True !!!
            export_mapper = self.unit_for(ExportMapper)
            map_record = export_mapper.map_record(binding)
            current_odoo_export_data = map_record.values(no_external_data=True)

            # Check if relevant odoo data changed since last export
            if cmp_payloads(last_sync_cmp_data, current_odoo_export_data):
                _logger.error("IMPORT: SKIPP IMPORT of '%s'! Odoo record data changed since last sync for binding "
                              "'%s', '%s'!" % (self.getresponse_id, binding._name, binding.id,))

                # FORCE EXPORT THE BINDING
                exporter = self.unit_for(GetResponseExporter)
                _logger.warning("IMPORT: FORCE EXPORT OF '%s' (binding '%s', '%s') BECAUSE A CONCURRENT WRITE WAS"
                                " DETECTED!" % (self.getresponse_id, binding._name, binding.id))
                exporter.run(binding.id)

                # SKIPP THE IMPORT
                return ("SKIPP IMPORT of '%s'! Odoo record data changed since last sync for binding '%s', '%s'!"
                        "\n\ncurrent_odoo_export_data:\n%s,\n\nlast_sync_cmp_data:\n%s"
                        "" % (self.getresponse_id, binding._name, binding.id, current_odoo_export_data,
                              last_sync_cmp_data))

        # A binding without compare data for binding updates should not exist!
        else:
            msg = ("IMPORT: Could not check '%s' for odoo data changes before import because binding.compare_data is"
                   " missing for binding '%s', '%s'! Continuing with import!"
                   "" % (self.getresponse_id, binding._name, binding.id))
            _logger.error(msg)
            return False

        # Continue with the import
        return False

    def _import_dependency(self, getresponse_id, binding_model,
                           importer_class=None, always=False):
        """ Import a dependency.

        The importer class is a class or subclass of
        :class:`GetResponseImporter`. A specific class can be defined.

        :param getresponse_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_cls: :class:`openerp.addons.connector.connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: GetResponseImporter
        :type importer_cls: :class:`openerp.addons.connector.connector.MetaConnectorUnit`
        :param always: if True, the record is updated even if it already
                       exists, note that it is still skipped if it has
                       not been modified on GetResponse since the last
                       update. When False, it will import it only when
                       it does not yet exist.
        :type always: boolean
        """
        if not getresponse_id:
            return
        if importer_class is None:
            importer_class = GetResponseImporter
        binder = self.binder_for(binding_model)
        if always or binder.to_openerp(getresponse_id) is None:
            importer = self.unit_for(importer_class, model=binding_model)
            importer.run(getresponse_id)

    def _import_dependencies(self):
        """ Import the dependencies for the record

        Import of dependencies can be done manually or by calling
        :meth:`_import_dependency` for each dependency.
        """
        return

    def _get_map_record(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.getresponse_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid.

        Raise `InvalidDataError`
        """
        return

    def skip_by_getresponse_data(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        return False

    def _get_binding(self):
        return self.binder.to_openerp(self.getresponse_id)

    def bind_before_import(self):
        """ Hook to be implemented in model specific importers to bind unbound existing records before import

        HINT: This will changed the import to an 'update' instead of an 'create'
        """
        return self.binding_record

    def skip_by_binding(self):
        if self.binding_record:
            filtered_binding = self.binder.get_bindings(domain=[('id', '=', self.binding_record.id)])
            if not filtered_binding:
                return _("Import was SKIPPED for binding (%s, %s) by binder.get_bindings()"
                         ) % (self.binding_record._name, self.binding_record.id)
        return False

    # ---------------------
    # CREATE RECORD IN ODOO
    # ---------------------
    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        # Add connector_no_export=True to prevent any GetResponse export
        binding_model_no_export = self.model.with_context(connector_no_export=True)
        # Create the binding record and therefore the regular odoo record (delegation inheritance) also
        binding = binding_model_no_export.create(data)
        return binding

    def create(self, data):
        """ Create an odoo record """
        # Validate getresponse record data before odoo record creation
        self._validate_data(data)
        new_binding = self._create(data)
        _logger.info("IMPORT: Binding '%s', '%s' created for GetResponse '%s'"
                     "" % (new_binding._name, new_binding.id, self.getresponse_id))
        return new_binding

    # ---------------------
    # UPDATE RECORD IN ODOO
    # ---------------------
    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        # Add connector_no_export={bind_model_name: [id]} to prevent GetResponse exports for this binding
        binding = binding.with_context(connector_no_export={binding._name: [binding.id]})
        # Update the binding record (and therefore the regular odoo record (delegation inheritance) also
        boolean_result = binding.write(data)
        return boolean_result

    def update(self, binding, data):
        """ Update an Odoo record """
        # Validate getresponse record data before odoo record update
        self._validate_data(data)
        boolean_result = self._update(binding, data)
        _logger.info("IMPORT: '%s', '%s' updated from GetResponse '%s' with result '%s'"
                     "" % (binding._name, binding.id, self.getresponse_id, boolean_result))
        return boolean_result

    def _update_binding_after_import(self, sync_data=None):
        assert self.binding_record, "self.binding_record is missing!"

        # Create the compare data based on the current odoo data after the import
        # ATTENTION: The export mapper would merge the current getresponse data with the current odoo data!
        #            !!! Therefore we need to set no_external_data=True !!! This should work perfectly because after
        #            an import the data must match the current GR data!
        export_mapper = self.unit_for(ExportMapper)
        map_record = export_mapper.map_record(self.binding_record)
        current_getresponse_update_payload = map_record.values(no_external_data=True)

        # Update the binding data
        self.binder.bind(self.getresponse_id, self.binding_record,
                         sync_data=sync_data, compare_data=current_getresponse_update_payload)

    def _import_related_bindings(self, *args, **kwargs):
        return

    def _after_import(self, *args, **kwargs):
        """ Hook called at the end of the import """
        return

    # -----------------
    # RUN/DO THE IMPORT
    # -----------------
    def run(self, getresponse_id, force=False, *args, **kwargs):
        """ Run the synchronization

        :param getresponse_id: identifier of the record in GetResponse
        """
        _logger.info("IMPORT: run() for external id %s" % getresponse_id)
        # Store the external id to import in self.getresponse_id
        self.getresponse_id = getresponse_id

        # READ THE DATA OF THE GETRESPONSE RECORD
        try:
            self.getresponse_record = self._get_getresponse_data()
        except IDMissingInBackend:
            # TODO: We may want to add an error and a status field to the binding model and extend .bind()
            #       with extra attributes so we could update the binding in case of errors. This would make it
            #       much easier to see which records have errors!!!
            return _('Record does no longer exist in GetResponse')

        # SKIP BY GETRESPONSE DATA
        # ------------------------
        skip_by_getresponse_data = self.skip_by_getresponse_data()
        if skip_by_getresponse_data:
            return skip_by_getresponse_data

        # Search for a binding record that has the external id (self.getresponse_id)
        self.binding_record = self._get_binding()

        # Bind to existing odoo records (or prepared bindings) before import
        self.binding_record = self.bind_before_import()

        # SKIP IMPORT BY BINDING
        # ----------------------
        # HINT: This will not be checked on create because obviously no binding would exists at this point
        if self.binding_record:
            skip_by_binding = self.skip_by_binding()
            if skip_by_binding:
                return skip_by_binding

        # SKIP IMPORT FOR UPDATES
        # -----------------------
        if not force:
            skip_import = self._skip_import_for_updates()
            if skip_import:
                return skip_import

        # Keep a lock on this import until the transaction is committed
        # The lock is kept since we have detected that the information will be updated into Odoo
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            getresponse_id,
        )
        self.advisory_lock_or_retry(lock_name)
        self._before_import()

        # -------------------
        # IMPORT DEPENDENCIES
        # -------------------
        self._import_dependencies()

        # Get a connector map record - based on the getresponse record in self.getresponse_record
        self.map_record = self._get_map_record()

        # ---------------------------------
        # UPDATE an existing binding record
        # ---------------------------------
        if self.binding_record:
            odoo_record_data = self._update_data(self.map_record)
            # Copy data to avoid side effects of added data (like sosync_write_date) on record update later on
            copy_of_data = deepcopy(odoo_record_data)
            update_result = self.update(self.binding_record, copy_of_data)

        # ---------------------------
        # CREATE a new binding record
        # ---------------------------
        else:
            odoo_record_data = self._create_data(self.map_record)
            # Copy data to avoid side effects of added data (like sosync_write_date) on record update later on
            copy_of_data = deepcopy(odoo_record_data)
            self.binding_record = self.create(copy_of_data)

        # --------------------------------------
        # UPDATE THE BINDING RECORD AFTER IMPORT
        # --------------------------------------
        self._update_binding_after_import(sync_data=odoo_record_data)

        # IMPORT RELATED BINDINGS
        # -----------------------
        if 'skip_import_related_bindings' not in kwargs:
            self._import_related_bindings(*args, **kwargs)

        # AFTER IMPORT HOOK
        # -----------------
        if 'skip_after_import' not in kwargs:
            self._after_import(*args, **kwargs)

        _logger.info("IMPORT: run() for external id %s DONE" % getresponse_id)


# HINT: This is called from DirectBatchImporter() and DelayedBatchImporter()
@job(default_channel='root.getresponse')
def import_record(session, model_name, backend_id, getresponse_id, force=False):
    """ Import a record from GetResponse """
    env = get_environment(session, model_name, backend_id)

    # ATTENTION: The GetResponseImporter class may be changed by the model specific implementation!
    #            The connector knows which classes to consider based on the _model_name of the class and the
    #            'model_name' in the args of import_record
    importer = env.get_connector_unit(GetResponseImporter)

    # Start the .run() method of the importer
    importer.run(getresponse_id, force=force)
