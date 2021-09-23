# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiPaymentAcquirer(FsoRestApiTestCase):
    _model_name = "payment.acquirer"

    def test_read_payment_acquirer_works(self):
        model = self.read_first_from_api()
        self.assertModel(model)

    def test_create_payment_acquirer_is_denied(self):
        response = self.create_via_api(data={
            "name": "Test Payment Acquirer"
        })
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)

    def test_update_payment_acquirer_is_denied(self):
        expected_name = "Test Payment Acquirer"
        model = self.read_first_from_api()

        self.assertModel(model)
        self.assertNotEqual(model["name"], expected_name)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "name": expected_name
        })
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)

    def test_delete_payment_acquirer_is_denied(self):
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
