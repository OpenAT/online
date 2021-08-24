# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiProductTemplate(FsoRestApiTestCase):
    _model_name = "product.template"

    def test_create_minimal_product_template_works(self):
        expected_name = "Test Product Template"
        response = self.create_via_api(data={
            "name": expected_name
        })
        model = response.json()

        self.assertEqual(response.status_code, self.HTTP_OK_CREATED)
        self.assertModel(model)

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.name, model["name"])

    def test_read_product_template_works(self):
        model = self.read_first_from_api()
        self.assertModel(model)

    def test_update_product_template_works(self):
        expected_name = "Test Product Template"
        model = self.read_first_from_api()

        self.assertNotEqual(model["name"], expected_name)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "name": expected_name
        })

        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_OK_NO_CONTENT)

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.name, expected_name)

    def test_delete_product_template_is_denied(self):
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
