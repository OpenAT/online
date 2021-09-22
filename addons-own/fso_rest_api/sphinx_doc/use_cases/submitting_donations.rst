.. _submitting_donations:

=====================
Submitting Donations
=====================

Overview
------------------

In order to submit a donation or a payment, the following process is required:

1) Create a :ref:`res_partner` containing the personal information
2) Create a :ref:`sale_order` including one or more :ref:`sale_order_line` for the order details
3) Create a :ref:`payment_transaction` for the payment details
4) Update the :ref:`sale_order` setting the `state` and `payment_tx_id`
5) Optional: send a :ref:`mail_message` with a comment for the organisation


Example
------------------

.. tabs::

    .. code-tab:: python

        # Fundraising Studio REST API Examples

        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Create a partner
        partner_data = {
            'firstname': 'Max',
            'lastname': 'Mustermann',
            'email': 'max@mustermann.com'
        }
        partner_response = requests.post(api_base_url + '/res.partner', auth=auth, json=partner_data)
        partner_id = partner_response.json()["id"]

        # Prepare the order lines, the example uses a product ID that was looked up manually
        product_id = 4
        # The lines data is a list of tuples, in the format (0, _, data)
        # First parameter 0 = add to list
        # Second parameter can be anything
        # Third parameter = dictionary with actual data
        sale_order_lines_data = [
            (0, False, {
                'name': 'Fight animal cruelty',
                'state': 'done',
                'product_id': product_id,
                'fs_origin': 'https://my-site.at/form',
                'price_unit': 55.25,
                'product_uos_qty': 1,
                'price_donate': 55.25,
            }),
        ]

        # Prepare the order, note the status 'draft'. The example uses an acquirer ID that was looked up manually
        acquirer_id = 4  # External payment
        sale_order_data = {
            'name': 'ORG123',
            'state': 'draft',
            'date_order': '2021-09-07 10:03:22',
            'date_confirm': '2021-09-07 10:03:45',
            'amount_total': 55.25,
            'partner_id': partner_id,
            'order_line': sale_order_lines_data,
            'payment_acquirer_id': acquirer_id,
        }
        sale_order_response = requests.post(api_base_url + '/sale.order', auth=auth, json=sale_order_data)
        sale_order_id = sale_order_response.json()["id"]

        # Prepare the payment, the IDs for country and currency were looked up manually
        country_id = 13  # Austria
        currency_id = 1  # EUR
        payment_transaction_data = {
            'acquirer_id': acquirer_id,
            'partner_country_id': country_id,
            'partner_lang': 'de_DE',
            'currency_id': currency_id,
            'state': 'done',
            'reference': 'ORG123',
            'acquirer_reference': 'Payment-System-ID-4711',
            'amount': 55.25,
            'sale_order_id': sale_order_id,
            'consale_provider_name': 'My Company',
            'consale_method': 'banktransfer',
            'consale_method_other': None,
            'consale_method_brand': None,
            'consale_method_banktransfer_provider': 'frst',
            'consale_method_account_owner': 'Max Mustermann',
            'consale_method_account_iban': 'AT990000000000000000',
            'consale_method_account_bic': None,
            'consale_method_account_bank': None,
            'consale_recurring_payment_provider': 'frst',
        }
        payment_transaction_response = requests.post(api_base_url + '/payment.transaction', auth=auth, json=payment_transaction_data)
        payment_transaction_id = payment_transaction_response.json()["id"]

        # Finally, update the sale order with the new payment transaction ID
        # and set the state to 'done'
        sale_order_update_data = {
            'state': 'done',
            'payment_tx_id': payment_transaction_id,
        }
        requests.put(api_base_url + '/sale.order/%s' % sale_order_id, auth=auth, json=sale_order_update_data)

        # Optional:
        # Send a comment for the organisation, subtype_id was looked up manually.
        # This can be used for detailed information on the donation. E.g., the product is
        # "Fight animal cruelty", but in the comment the donor specifies to only support dogs.
        subtype_id = 61  # FS-Online Question / Survey
        message_data = {
            'body': 'Use my donation for dogs only.',
            'model': 'sale.order',
            'res_id': sale_order_id,
            'type': 'comment',
            'subtype_id': subtype_id
        }
        requests.post(api_base_url + '/mail.message', auth=auth, json=message_data)
