# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiProductProduct(FsoRestApiTestCase):
    _model_name = "product.product"

    def create_product_product_via_api(self, code):
        template_id = self.read_first_from_api(model="product.template")["id"]
        response = self.create_via_api(data={
            "product_tmpl_id": template_id,
            "default_code": code
        })
        model = response.json()
        return int(model["id"])

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

    def test_update_own_product_product_works(self):
        product_id = self.create_product_product_via_api("Test Code")

        expected_code = "New code"
        model = self.read_from_api(id=product_id)

        self.assertNotEqual(model["default_code"], expected_code)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "default_code": expected_code
        })

        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_OK_NO_CONTENT)

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.default_code, expected_code)

    def test_update_others_product_product_is_denied(self):
        expected_code = "Test Code"
        model = self.read_first_from_api()

        self.assertModel(model)
        self.assertNotEqual(model["default_code"], expected_code)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "default_code": expected_code
        })

        self.assertTrue(not str(response.status_code).startswith("2"))
        self.assertTrue("Access Denied" in response.content)

    def test_delete_product_product_is_denied(self):
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
