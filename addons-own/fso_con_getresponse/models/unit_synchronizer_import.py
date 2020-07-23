# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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

Importers for GetResponse.

An import can be skipped if changes in both system are detected. (Concurrent write)

ATTENTION: Call the ``bind`` method even if the records are already bound, to update the last sync date.

"""

import logging
from openerp.tools.translate import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.exception import IDMissingInBackend
from .connector import get_environment

_logger = logging.getLogger(__name__)


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

        # TODO: Compare the last synced data 'sync_data' of the binding record with the current getresponse record data
        #       Return True if the data still matches. This is basically a 'field' compare to overcome the limitation
        #       of GetResponse of not having a 'write_date' or 'last_updated_at' for every object
        #       For the prototype we just return False to always trigger a sync!
        return False

    def _import_dependency(self, getresponse_id, binding_model,
                           importer_class=None, always=False):
        """ Import a dependency.

        The importer class is a class or subclass of
        :class:`GetResponseImporter`. A specific class can be defined.

        :param getresponse_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_cls: :class:`openerp.addons.connector.\
                                     connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: GetResponseImporter
        :type importer_cls: :class:`openerp.addons.connector.\
                                    connector.MetaConnectorUnit`
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

    def _must_skip(self):
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

        return

    def _get_binding(self):
        return self.binder.to_openerp(self.getresponse_id, browse=True)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    # CREATE RECORD IN ODOO
    # ---------------------
    def _create(self, data):
        """ Create the odoo record """
        # Validate getresponse record data before odoo record creation
        self._validate_data(data)
        # Get the correct model and prevent export job generation via connector_no_export=True
        model = self.model.with_context(connector_no_export=True)
        # Create the new binding record (and therefore the regular odoo record (delegation inheritance) also
        binding = model.create(data)
        _logger.debug('%d created from getresponse %s', binding, self.getresponse_id)
        return binding

    # UPDATE RECORD IN ODOO
    # ---------------------
    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an OpenERP record """
        # Validate getresponse record data before odoo record update
        self._validate_data(data)
        # Add connector_no_export=True to the env of the binding record to prevent export job creation
        binding = binding.with_context(connector_no_export=True)
        # Update the binding record (and therefore the regular odoo record (delegation inheritance) also
        binding.write(data)
        _logger.debug('%d updated from getresponse %s', binding, self.getresponse_id)
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

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

        # Get the data of the GetResponse Record (self.backend_adapter.read(self.getresponse_id))
        try:
            self.getresponse_record = self._get_getresponse_data()
        except IDMissingInBackend:
            return _('Record does no longer exist in GetResponse')

        # Check if we must skip the import (e.g. on changes in both systems)
        skip = self._must_skip()
        if skip:
            return skip

        # Get the odoo binding model record
        binding = self._get_binding()

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

        # Update an existing record in odoo
        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        # Create a new record in odoo
        else:
            record = self._create_data(map_record)
            binding = self._create(record)

        # Call the binder again to update sync_date and sync_data
        # TODO: Add sync_data to the binder - not implemented yet
        self.binder.bind(self.getresponse_id, binding)

        # After import hook
        self._after_import(binding)


class BatchImporter(Importer):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    def run(self, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters)
        for record_id in record_ids:
            self._import_record(record_id)

    def _import_record(self, record_id):
        """ Import a record directly or delay the import of the record.

        Method to implement in sub-classes.
        """
        raise NotImplementedError


class DirectBatchImporter(BatchImporter):
    """ Import the records directly, without delaying the jobs. """
    _model_name = None

    def _import_record(self, record_id):
        """ Import the record directly """
        import_record(self.session,
                      self.model._name,
                      self.backend_record.id,
                      record_id)


class DelayedBatchImporter(BatchImporter):
    """ Delay import of the records """
    _model_name = None

    def _import_record(self, record_id, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            record_id,
                            **kwargs)


@job(default_channel='root.getresponse')
def import_batch(session, model_name, backend_id, filters=None):
    """ Prepare a batch import of records from GetResponse """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchImporter)
    importer.run(filters=filters)


@job(default_channel='root.getresponse')
def import_record(session, model_name, backend_id, getresponse_id, force=False):
    """ Import a record from GetResponse """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(GetResponseImporter)
    importer.run(getresponse_id, force=force)
