# -*- coding: utf-8 -*-
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from getresponse.client import GetResponse


class GetResponseCRUDAdapter(CRUDAdapter):
    """ Adapter to talk with GetResponse API. Implements the basic CRUD methods and search """

    def __init__(self, connector_env):
        """

        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(GetResponseCRUDAdapter, self).__init__(connector_env)
        backend = self.backend_record

        # TODO: maybe i should rename this this to getresponse_adapter for clarification
        self.getresponse = GetResponse(backend.api_key)

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError
