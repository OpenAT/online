# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiSaleOrderLine(FsoRestApiTestCase):
    _model_name = "sale.order.line"

    def create_sale_order(self, partner_id, order_name):
        response = self.create_via_api(model="sale.order", data={
            "partner_id": partner_id,
            "name": order_name
        })
        model = response.json()
        return model

    def test_create_minimal_sale_order_line_works(self):
        expected_origin = "https://localhost/test"
        partner = self.read_first_from_api(model="res.partner")
        order = self.create_sale_order(partner["id"], "TEST1")
        product = self.read_first_from_api(model="product.product")

        response = self.create_via_api(data={
            "order_id": order["id"],
            "product_id": product["id"],
            "fs_origin": expected_origin
        })
        model = response.json()

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.fs_origin, model["fs_origin"])

    def test_read_sale_order_line_works(self):
        model = self.read_first_from_api()
        self.assertModel(model)

    def test_update_sale_order_line_is_denied(self):
        expected_origin = "https://localhost/test"
        model = self.read_first_from_api()

        self.assertModel(model)
        self.assertNotEqual(model["fs_origin"], expected_origin)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "fs_origin": expected_origin
        })
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)

    def test_delete_sale_order_line_is_denied(self):
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
