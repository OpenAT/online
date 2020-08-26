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
from openerp.tools.translate import _

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.exception import IDMissingInBackend

from .helper_connector import get_environment, add_checkpoint
from .backend import getresponse

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

    def batch_run(self, filters=None, delay=False, **kwargs):
        """ Run the synchronization """

        # ------------------------------
        # SEARCH FOR GETRESPONSE RECORDS
        # ------------------------------
        getresponse_record_ids = self.backend_adapter.search(filters)

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

    def _get_getresponse_data(self):
        """ Return the raw Getresponse object/data for ``self.getresponse_id`` """
        return self.backend_adapter.read(self.getresponse_id)

    def _before_import(self):
        """ Hook called before the import, when we have the GetResponse data"""

    def _is_uptodate(self, binding):
        """ Return True if the import should be skipped because it is already up-to-date """
        # Make sure we already have the getresponse record
        assert self.getresponse_record

        # Unbound (new) records can never be up-to-date
        if not binding:
            return False

        # Compare the current getresponse data with the data stored at the last sync!
        current_getresponse_data = self._map_data().values()
        last_sync_data = json.loads(binding.sync_data, encoding='utf8') if binding.sync_data else {}
        if cmp(current_getresponse_data, last_sync_data) == 0:
            _logger.info("Bound record data did not change (%s, %s)! Import will be skipped!"
                         "" % (binding._model, binding.id))
            return True

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
                       not been modified on GetResponce since the last
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

    def _map_data(self):
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

        # TODO: Compare the last synced data 'sync_data' of the binding record with the current getresponse record data
        #       Return True if the data still matches. This is basically a 'field' compare to overcome the limitation
        #       of GetResponse of not having a 'write_date' or 'last_updated_at' for every object
        #       For the prototype we just return False to always trigger a sync!

        return False

    def _get_binding(self):
        return self.binder.to_openerp(self.getresponse_id)

    def bind_before_import(self, binding):
        return binding

    def skip_by_binding(self, binding):
        binding = self.binder.get_bindings(filter=[('id', '=', binding.id)])
        if not binding:
            return _("Import was skipped for binding (%s, %s) by binder.get_bindings()") % (binding._name, binding.id)

        return False

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    # ---------------------
    # CREATE RECORD IN ODOO
    # ---------------------
    def _create(self, data):
        """ Create the odoo record """
        # Validate getresponse record data before odoo record creation
        self._validate_data(data)

        # Add connector_no_export=True to prevent any GetResponse export
        model = self.model.with_context(connector_no_export=True)

        # Create the new binding record (and therefore the regular odoo record (delegation inheritance) also
        binding = model.create(data)
        _logger.debug('%d created from getresponse %s', binding, self.getresponse_id)
        return binding

    # ---------------------
    # UPDATE RECORD IN ODOO
    # ---------------------
    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an OpenERP record """
        # Validate getresponse record data before odoo record update
        self._validate_data(data)

        # Add connector_no_export={bind_model_name: [id]} to prevent GetResponse exports for this binding
        binding = binding.with_context(connector_no_export={binding._name: [binding.id]})

        # Update the binding record (and therefore the regular odoo record (delegation inheritance) also
        binding.write(data)
        _logger.debug('%d updated from getresponse %s', binding, self.getresponse_id)
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    # -----------------
    # RUN/DO THE IMPORT
    # -----------------
    def run(self, getresponse_id, force=False):
        """ Run the synchronization

        :param magento_id: identifier of the record on Magento
        """
        self.getresponse_id = getresponse_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            getresponse_id,
        )

        # Get the data of the GetResponse Record: will use "self.backend_adapter.read(self.getresponse_id)"
        # HINT: This situation may only exist if we import a record before we export it or the record was delete
        #       just now (so between the read-list-of-records and the processing of one record of the list)
        try:
            self.getresponse_record = self._get_getresponse_data()
        except IDMissingInBackend:
            # TODO: We may want to add an error and a status field to the binding model and extend .bind()
            #       with extra attributes so we could update the binding in case of errors. This would make it
            #       much easier to see which records have errors!!!
            return _('Record does no longer exist in GetResponse')

        # Skip import based on the returned GetResponse record data
        skip_by_getresponse_data = self.skip_by_getresponse_data()
        if skip_by_getresponse_data:
            return skip_by_getresponse_data

        # Search for a binding record that has the external id (self.getresponse_id)
        binding = self._get_binding()

        # Bind to existing records (or use prepared bindings) before import
        binding = self.bind_before_import(binding)

        # Skip import based on the binding (based on odoo record data filtered out by binder.get_bindings())
        if binding:
            skip_by_binding = self.skip_by_binding(binding)
            if skip_by_binding:
                return skip_by_binding

        # Check the data in odoo is already up to date and skipp import if so
        if not force and self._is_uptodate(binding):
            return _('Already up-to-date.')

        # Keep a lock on this import until the transaction is committed
        # The lock is kept since we have detected that the information will be updated into Odoo
        self.advisory_lock_or_retry(lock_name)
        self._before_import()

        # Import the missing linked resources
        self._import_dependencies()

        # Get the data from the GetResponse record already prepared (mapped) for the odoo record
        map_record = self._map_data()
        update_data = self._update_data(map_record)

        # UPDATE an existing record in odoo
        if binding:
            self._update(binding, update_data)

        # CREATE a new record in odoo
        else:
            create_data = self._create_data(map_record)
            binding = self._create(create_data)

        # Call the binder again to update the binding and the 'sync_data' for concurrent write detection
        # ATTENTION: We store only the fields without '@only_create' mapped fields since those fields seems unneeded
        #            for the data comparison TODO: Make sure to check if this is true for every synced model!
        self.binder.bind(self.getresponse_id, binding, sync_data=update_data)

        # After import hook
        self._after_import(binding)


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
