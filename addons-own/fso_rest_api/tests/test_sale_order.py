# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiSaleOrder(FsoRestApiTestCase):
    _model_name = "sale.order"

    def test_create_minimal_sale_order_works(self):
        partner = self.read_first_from_api(model="res.partner")

        expected_name = "TEST1"
        response = self.create_via_api(data={
            "partner_id": partner["id"],
            "name": expected_name
        })
        model = response.json()

        self.assertEqual(response.status_code, self.HTTP_OK_CREATED)
        self.assertModel(model)

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.name, model["name"])

    def test_read_sale_order_works(self):
        model = self.read_first_from_api()
        self.assertModel(model)

    def test_update_sale_order_works(self):
        expected_name = "TEST1"
        model = self.read_first_from_api()

        self.assertModel(model)
        self.assertNotEqual(model["name"], expected_name)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "name": expected_name
        })
        self.assertEqual(response.status_code, self.HTTP_OK_NO_CONTENT)

    def test_delete_sale_order_is_denied(self):
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
