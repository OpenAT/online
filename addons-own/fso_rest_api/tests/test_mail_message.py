# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiMailMessage(FsoRestApiTestCase):
    _model_name = "mail.message"

    def test_read_mail_message_is_denied(self):
        response = self.api_request(
            "GET",
            self.get_model_url(self._model_name),
            auth=self.api_auth)

        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)

    # Should be allowed
    def test_create_mail_message_works(self):
        response = self.create_via_api(data={
            "body": "Test message"
        })
        self.assertEqual(response.status_code, self.HTTP_OK_CREATED)

    def test_update_mail_message_is_denied(self):
        model_obj = self.phantom_env[self._model_name]
        model = model_obj.search([], order="id", limit=1)

        expected_body = "Test message"
        self.assertNotEqual(model.body, expected_body)

        response = self.update_via_api(data={
            "id": int(model.id),
            "body": expected_body
        })
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)

    def test_delete_mail_message_is_denied(self):
        model_obj = self.phantom_env[self._model_name]
        model = model_obj.search([], order="id", limit=1)

        response = self.delete_via_api(model.id)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
