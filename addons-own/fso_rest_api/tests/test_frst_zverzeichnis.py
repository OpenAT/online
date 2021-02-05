# -*- coding: utf-8 -*-
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

class TestFsoRestApiFrstzVerzeichnis(HttpCase):

    _model_name = "frst.zverzeichnis"

    def setUp(self):
        super(TestFsoRestApiFrstzVerzeichnis, self).setUp()

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

    def create_zverzeichnis_by_rest_api(self, data=None):
        create_method = "POST"
        create_url = self.get_model_url(self._model_name)
        if data is None:
            data = {"verzeichnisname": "My Directory"}
        create_response = self.api_request(create_method, create_url, auth=self.api_auth, json=data)

        # Raise a request exception, if the request is anything but created
        if create_response.status_code != pinguin.CODE__created:
            raise RequestException(create_response.text)

        model_data = create_response.json()
        model_id = model_data["id"]
        model = self.phantom_env[self._model_name].browse([model_id])
        self.assertEqual(model.verzeichnisname, data["verzeichnisname"])
        return model

    def test_create_minimal_cds_works(self):
        model = self.create_zverzeichnis_by_rest_api()

        # Assert the existing person could NOT be deleted
        # HINT: Delete partner created by an other user should NOT work (check ir.rule)
        # HINT: code 204 = successful delete
        self.assertTrue(model.id)

    def test_create_cds_with_wrong_bezeichnungstyp_fails(self):
        # Expect a request exception, "X" is an invalid value
        with self.assertRaises(RequestException) as e:
            self.create_zverzeichnis_by_rest_api(
                {"verzeichnisname": "My Directory",
                 "bezeichnungstyp_id": "X"})
