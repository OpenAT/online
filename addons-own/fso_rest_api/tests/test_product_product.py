# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiProductProduct(FsoRestApiTestCase):
    _model_name = "product.product"

    def test_create_minimal_product_product_works(self):
        expected_code = "Test Code"
        template = self.read_first_from_api(model="product.template")

        response = self.create_via_api(data={
            "product_tmpl_id": template["id"],
            "default_code": expected_code
        })
        model = response.json()

        self.assertEqual(response.status_code, self.HTTP_OK_CREATED)
        self.assertModel(model)

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.default_code, model["default_code"])

    def test_read_product_product_works(self):
        model = self.read_first_from_api()
        self.assertModel(model)

    def test_update_product_product_works(self):
        expected_code = "Test Code"
        model = self.read_first_from_api()

        self.assertNotEqual(model["default_code"], expected_code)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "default_code": expected_code
        })

        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_OK_NO_CONTENT)

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.default_code, expected_code)

    def test_delete_product_product_is_denied(self):
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
