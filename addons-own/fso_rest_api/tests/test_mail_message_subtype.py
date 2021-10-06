# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiMailMessageSubtype(FsoRestApiTestCase):
    _model_name = "mail.message.subtype"

    def test_read_mail_message_subtype_works(self):
        model = self.read_first_from_api()
        self.assertModel(model)

    def test_create_mail_message_subtype_is_denied(self):
        response = self.create_via_api(data={
            "name": "Test Subtype"
        })
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)

    def test_update_mail_message_subtype_is_denied(self):
        expected_name = "Test Subtype"
        model = self.read_first_from_api()

        self.assertModel(model)
        self.assertNotEqual(model["name"], expected_name)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "name": expected_name
        })
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)

    def test_delete_mail_message_subtype_is_denied(self):
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
