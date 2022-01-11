# -*- coding: utf-8 -*-

from fso_rest_api_test_case import FsoRestApiTestCase

import logging
logger = logging.getLogger(__name__)


class TestFsoRestApiPaymentTransaction(FsoRestApiTestCase):
    _model_name = "payment.transaction"

    def create_sale_order(self, partner_id, payment_tx_id, order_name):
        response = self.create_via_api(model="sale.order", data={
            "partner_id": partner_id,
            "payment_tx_id": payment_tx_id,
            "name": order_name
        })
        model = response.json()
        return model

    def create_payment_transaction(self, ref, amount):
        country = self.read_first_from_api(model="res.country")
        currency = self.read_first_from_api(model="res.currency")
        acquirer = self.read_first_from_api(model="payment.acquirer")
        response = self.create_via_api(data={
            "acquirer_id": acquirer["id"],
            "partner_country_id": country["id"],
            "currency_id": currency["id"],
            "reference": ref,
            "amount": amount
        })
        model = response.json()
        return model

    def test_create_minimal_payment_transaction_works(self):
        expected_ref = "TEST1"
        expected_amount = 15.25
        model = self.create_payment_transaction(expected_ref, expected_amount)

        actual = self.phantom_env[self._model_name].browse([int(model["id"])])
        self.assertEqual(actual.reference, model["reference"])
        self.assertEqual(actual.amount, model["amount"])

    def test_read_payment_transaction_works(self):
        _ = self.create_payment_transaction("TEST1", 1.0)
        model = self.read_first_from_api()
        self.assertModel(model)

    def test_update_payment_transaction_works_for_own(self):
        _ = self.create_payment_transaction("TEST1", 1.0)
        expected_ref = "TEST2"
        model = self.read_first_from_api()

        self.assertModel(model)
        self.assertNotEqual(model["reference"], expected_ref)

        response = self.update_via_api(data={
            "id": int(model["id"]),
            "reference": expected_ref
        })
        self.assertEqual(response.status_code, self.HTTP_OK_NO_CONTENT)

    def test_update_payment_transaction_other_is_denied(self):
        country = self.read_first_from_api(model="res.country")
        currency = self.read_first_from_api(model="res.currency")
        acquirer = self.read_first_from_api(model="payment.acquirer")
        partner = self.env["res.partner"].search([['country_id', '!=', False]], limit=1)
        payment_transaction_obj = self.phantom_env[self._model_name].sudo()
        other_transaction = payment_transaction_obj.create({
            "partner_id": partner["id"],
            "acquirer_id": acquirer["id"],
            "partner_country_id": country["id"],
            "currency_id": currency["id"],
            "reference": "TEST1",
            "amount": 41.50,
        })

        expected_amount = 999
        response = self.update_via_api(data={
            "id": int(other_transaction["id"]),
            "amount": expected_amount
        })

        reloaded_payment_transaction = self.phantom_env[self._model_name].browse(int(other_transaction["id"]))
        logger.info("RECORD OWNER of payment.transaction %s = %s" % (reloaded_payment_transaction.id, reloaded_payment_transaction.create_uid.id))
        self.assertNotEqual(reloaded_payment_transaction.amount, expected_amount)
        self.assertEqual(response.status_code, self.HTTP_REJECTED)

    def test_delete_payment_transaction_is_denied(self):
        _ = self.create_payment_transaction("TEST1", 1.0)
        model = self.read_first_from_api()
        response = self.delete_via_api(model["id"])
        self.assertModel(model)
        self.assertEqual(response.status_code, self.HTTP_FORBIDDEN)
