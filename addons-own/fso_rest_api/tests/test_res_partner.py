# -*- coding: utf-8 -*-
from openerp.tests.common import HttpCase, get_db_name
from openerp import api

# For http codes
from openerp.addons.openapi.controllers import pinguin

import requests
from requests.auth import HTTPBasicAuth
from urlparse import urljoin

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiResPartner(HttpCase):

    def setUp(self):
        super(TestFsoRestApiResPartner, self).setUp()

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

        # Create res.partner
        self.partner_max = self.phantom_env['res.partner'].create({
            'name': u"Max Testermann",
            'email': u"max@testermann.com"
        })

    def api_request(self, method, url, auth=None, json=None, timeout=5):
        logger.info("%s: %s" % (method, url))
        self.session = requests.Session()
        # Use the magic session_id stored by HTTPCase so that all changes are rolled back!
        self.session.cookies["session_id"] = self.session_id
        return self.session.request(method, url, auth=auth, json=json, timeout=timeout)

    def test_01_deny_delete_existing_partner(self):
        method = "DELETE"
        api_url = self.api_base_url + '/res.partner/' + str(self.partner_max.id)
        response = self.api_request(method, api_url, auth=self.api_auth)

        # Assert the existing person could NOT be deleted
        # HINT: Delete partner created by an other user should NOT work (check ir.rule)
        # HINT: code 204 = successful delete
        self.assertTrue(not str(response.status_code).startswith("2"))

    def test_02_create_and_delete_own_partner(self):
        # Create a partner
        create_method = "POST"
        create_url = self.api_base_url + '/res.partner/'
        data = {"firstname": "Tester",
                "lastname": "ToBeDeleted",
                "email": "tester@tobedeleted.com"}
        create_response = self.api_request(create_method, create_url, auth=self.api_auth, json=data)

        self.assertTrue(create_response.status_code == pinguin.CODE__created)

        # TODO: "id" is not in the returned dict ?!?
        partner_data = create_response.json()
        partner_id = partner_data["id"]
        partner = self.phantom_env['res.partner'].browse([partner_id])
        self.assertEqual(partner.lastname, data["lastname"])

        # Delete the created partner
        # HINT: Delete own partner should work (check ir.rule)
        # HINT: pinguin.CODE__ok_no_content = 204 = successful delete
        delete_method = "DELETE"
        delete_url = self.api_base_url + '/res.partner/' + str(partner_id)
        delete_response = self.api_request(delete_method, delete_url, auth=self.api_auth)
        self.assertEqual(delete_response.status_code, pinguin.CODE__ok_no_content)
