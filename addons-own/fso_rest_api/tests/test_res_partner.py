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

        # Create res.partner by the admin user
        self.partner_max = self.phantom_env['res.partner'].create({
            'name': u"Max Testermann",
            'email': u"max@testermann.com"
        })

    # ------
    # HELPER
    # ------
    def api_request(self, method, url, auth=None, json=None, timeout=5):
        logger.info("%s: %s" % (method, url))
        self.session = requests.Session()
        # Use the magic session_id stored by HTTPCase so that all changes are rolled back!
        self.session.cookies["session_id"] = self.session_id
        return self.session.request(method, url, auth=auth, json=json, timeout=timeout)

    def create_partner_by_rest_api(self, data=None):
        create_method = "POST"
        create_url = self.api_base_url + '/res.partner/'
        if data is None:
            data = {"firstname": "Tester",
                    "lastname": "ToBeDeleted",
                    "email": "tester@tobedeleted.com"}
        create_response = self.api_request(create_method, create_url, auth=self.api_auth, json=data)
        self.assertTrue(create_response.status_code == pinguin.CODE__created)
        partner_data = create_response.json()
        partner_id = partner_data["id"]
        partner = self.phantom_env['res.partner'].browse([partner_id])
        self.assertEqual(partner.lastname, data["lastname"])
        return partner

    # -----
    # TESTS
    # -----
    def test_01_deny_delete_other_partner(self):
        # Try to delete a partner of an other user
        method = "DELETE"
        api_url = self.api_base_url + '/res.partner/' + str(self.partner_max.id)
        response = self.api_request(method, api_url, auth=self.api_auth)

        # Assert the existing person could NOT be deleted
        # HINT: Delete partner created by an other user should NOT work (check ir.rule)
        # HINT: code 204 = successful delete
        self.assertTrue(not str(response.status_code).startswith("2"))

    def test_02_create_and_delete_own_partner(self):
        # Delete own partner
        # HINT: Delete own partner should work (check ir.rule)
        # HINT: pinguin.CODE__ok_no_content = 204
        partner = self.create_partner_by_rest_api()
        delete_method = "DELETE"
        delete_url = self.api_base_url + '/res.partner/' + str(partner.id)
        delete_response = self.api_request(delete_method, delete_url, auth=self.api_auth)

        # Assert that the deletion of the partner was successful
        self.assertEqual(delete_response.status_code, pinguin.CODE__ok_no_content)

    def test_03_deny_update_readonly_fields(self):
        # Try to update a readonly (in readonly_fields_id) field of the partner
        partner = self.create_partner_by_rest_api()
        update_method = "PUT"
        update_url = self.api_base_url + '/res.partner/' + str(partner.id)
        update_data = {
            "main_personemail_id": 1
        }
        update_response = self.api_request(update_method, update_url, auth=self.api_auth, json=update_data)

        # Assert that the update was denied because of field permissions
        self.assertTrue(not str(update_response.status_code).startswith("2"))
        self.assertTrue("Field Permissions" in update_response.content)

    def test_04_update_own_partner(self):
        partner = self.create_partner_by_rest_api()
        update_method = "PUT"
        update_url = self.api_base_url + '/res.partner/' + str(partner.id)
        update_data = {
            "lastname": "Builder",
            "email": "bob@builder.com"
        }
        update_response = self.api_request(update_method, update_url, auth=self.api_auth, json=update_data)
        self.assertEqual(update_response.status_code, pinguin.CODE__ok_no_content)
        updated_partner_response = self.api_request("GET", update_url, auth=self.api_auth)
        updated_partner_data = updated_partner_response.json()
        self.assertTrue(all(update_data[k] == updated_partner_data[k] for k in update_data.keys()))

    def test_05_update_other_partner(self):
        update_method = "PUT"
        update_url = self.api_base_url + '/res.partner/' + str(self.partner_max.id)
        update_data = {
            "lastname": "Builder",
            "email": "bob@builder.com"
        }
        update_response = self.api_request(update_method, update_url, auth=self.api_auth, json=update_data)
        self.assertEqual(update_response.status_code, pinguin.CODE__ok_no_content)
        updated_partner_response = self.api_request("GET", update_url, auth=self.api_auth)
        updated_partner_data = updated_partner_response.json()
        self.assertTrue(all(update_data[k] == updated_partner_data[k] for k in update_data.keys()))
