# -*- coding: utf-8 -*-
from ctypes import ArgumentError

from requests import RequestException

from openerp.tests.common import HttpCase, get_db_name
from openerp import api

# For http codes
from openerp.addons.openapi.controllers import pinguin

import requests
from requests.auth import HTTPBasicAuth
from urlparse import urljoin

import logging
logger = logging.getLogger(__name__)


class FsoRestApiTestCase(HttpCase):
    # Map & unpack constants form pinguin for easier access
    HTTP_OK = pinguin.CODE__success
    HTTP_OK_CREATED = pinguin.CODE__created
    HTTP_OK_ACCEPTED = pinguin.CODE__accepted
    HTTP_OK_NO_CONTENT = pinguin.CODE__ok_no_content
    HTTP_REJECTED, _ = pinguin.CODE__server_rejects
    HTTP_UNAUTHORIZED, _, _ = pinguin.CODE__no_user_auth
    HTTP_FORBIDDEN, _, _ = pinguin.CODE__method_blocked

    # Override in derived
    _model_name = None

    # Initialized by setUp()
    db_name = None
    phantom_env = None
    base_url = None
    api_demo_user = None,
    api_auth = None,
    api_namespace = None,
    api_base_url = None,
    session = None

    def setUp(self):
        super(FsoRestApiTestCase, self).setUp()

        # Creat a new odoo environment since this is a "HttpCase"
        self.db_name = get_db_name()
        self.phantom_env = api.Environment(self.registry.test_cr, self.uid, {})

        # Make sure language de_DE is installed
        if not self.phantom_env['res.lang'].search([('code', '=', 'de_DE')]):
            self.phantom_env['res.lang'].load_lang('de_DE')

        # Instance base url
        self.base_url = self.phantom_env['ir.config_parameter'].get_param('web.base.url')

        # FRST REST API data
        self.api_demo_user = self.phantom_env.ref("fso_rest_api.frst_api_user")
        self.api_auth = HTTPBasicAuth(self.api_demo_user.login, self.api_demo_user.openapi_token)
        self.api_namespace = self.phantom_env.ref("fso_rest_api.frst_rest_api_namespace")
        self.api_base_url = urljoin(self.base_url, "api/v1/" + self.api_namespace.name)

    def get_model_url(self, model):
        return self.api_base_url + "/" + model

    def api_request(self, method, url, auth=None, json=None, timeout=5):
        logger.info("%s: %s" % (method, url))
        self.session = requests.Session()
        # Use the magic session_id stored by HTTPCase so that all changes are rolled back!
        self.session.cookies["session_id"] = self.session_id
        return self.session.request(method, url, auth=auth, json=json, timeout=timeout)

    def create_via_api(self, model=None, data=None):
        """ Creates the specified model with the supplied data via the REST API.
        :param model: Optional model name. If None, self._model_name will be used.
        :param data: Data to be sent to the API.
        :return: Returns the HTTP response.
        """

        if not model:
            model = self._model_name

        if not data:
            raise ArgumentError('Keyword argument "data" requires a value.')

        create_url = self.get_model_url(model)
        response = self.api_request("POST", create_url, auth=self.api_auth, json=data)
        return response

    def read_first_from_api(self, model=None):
        """ Reads the first entry for the given model from the REST API.
        :param model: Optional model name. If None, self._model_name will be used.
        :return: Returns the data for the first entry.
        """

        if not model:
            model = self._model_name

        response = self.api_request(
            "GET",
            self.get_model_url(model),
            auth=self.api_auth)

        model_data = response.json()[0]
        return model_data

    def read_from_api(self, id=None, model=None):
        """ Reads the entry with the specified id for the given model from the REST API.
        :param id: The model ID
        :param model: Optional model name. If None, self._model_name will be used.
        :return: Returns the data for the specified entry.
        """

        if not model:
            model = self._model_name

        model_id = int(id)
        response = self.api_request(
            "GET",
            self.get_model_url(model) + "/%s" % model_id,
            auth=self.api_auth)

        model_data = response.json()
        return model_data

    def update_via_api(self, model=None, data=None):
        """ Updates the entry with the specified id for the given model via the REST API.
        :param model: Optional model name. If None, self._model_name will be used.
        :param data: Data to be sent to the API.
        :return: Returns the HTTP response.
        """
        if not model:
            model = self._model_name

        if not data:
            raise ArgumentError('Keyword argument "data" requires a value.')

        model_id = int(data["id"])
        response = self.api_request(
            "PUT",
            self.get_model_url(model) + "/%s" % model_id,
            auth=self.api_auth,
            json=data)

        return response

    def delete_via_api(self, id=None, model=None):
        """ Deletes the specified entry for the given model via the REST API.
        :param id: The model ID
        :param model: Optional model name. If None, self._model_name will be used.
        :return: Returns the HTTP response.
        """
        if not model:
            model = self._model_name

        model_id = int(id)
        response = self.api_request(
            "DELETE",
            self.get_model_url(model) + "/%s" % model_id,
            auth=self.api_auth)

        return response

    def assertModel(self, data):
        """ Helper, asserts that the specified dictionary is a model. """
        self.assertTrue(data["id"])
        self.assertTrue(len(data) > 1)
