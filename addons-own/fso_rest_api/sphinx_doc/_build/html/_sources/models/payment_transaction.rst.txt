.. _payment_transaction:

=========================================
payment.transaction
=========================================

Represents an actual payment, including all the payment specific information.


Special fields
--------------

``acquirer_id``
"""""""""""""""""""""""
The foreign key of the :ref:`payment_acquirer`.

.. important:: Use `External Payment (Connector Sale)` if

    - You are processing payments yourself
    - You send a direct debit order, to be processed by DataDialog

``state``
""""""""""""""""""""
The state of the transaction. Can be either:

- ``done`` The payment was successfully processed. **Use this for all payments NOT processed by DataDialog.**
- ``draft`` Payment still in draft
- ``pending`` Payment is in progress. **Use this for direct debit donations processed by DataDialog**
- ``error`` Error during payment
- ``cancel`` Payment was cancelled

``reference``
""""""""""""""""""""
Free text. This should match the ``name`` of the corresponding :ref:`sale_order`.

``acquirer_reference``
""""""""""""""""""""""
Free text. This should match the unique transaction identifier provided by the payment system.

``esr_reference_number``
""""""""""""""""""""""""
Free text. Postfinance unique identifier the transaction.

``amount``
""""""""""""""""""""
The monetary amount paid or donated.

``consale_provider_name``
"""""""""""""""""""""""""""""""""""""""""
External service and/or payment provider name. For example: My Company/Stripe

``consale_method``
"""""""""""""""""""""""""""""""""""""""""
Can be one of these values:

- ``paypal`` PayPal
- ``directdebit`` Direct debit
- ``applepay`` Apple Pay
- ``googlepay`` Google Pay
- ``banktransfer`` Bank transfer
- ``creditcard`` Credit card
- ``other`` When using this, specify the payment method in ``consale_method_other``

``consale_method_other``
"""""""""""""""""""""""""""""""""""""""""
When using ``consale_method`` = ``other``, use this text field to specify the payment method.

``consale_method_brand``
"""""""""""""""""""""""""""""""""""""""""
The brand name for the payment method. E.g., if the ``consale_method`` = ``creditcard``,
``consale_method_brand`` could be ``Visa``, or ``Mastercard``.


``consale_method_directdebit_provider``
"""""""""""""""""""""""""""""""""""""""""
When the ``consale_method`` = ``directdebit``, specify one of these values

- ``frst`` If DataDialog is supposed to handle the direct debit
- ``external`` If the direct debit is handled by yourself or externally

``consale_method_account_owner``
"""""""""""""""""""""""""""""""""""""""""
The full name of the bank account owner.

``consale_method_account_iban``
"""""""""""""""""""""""""""""""""""""""""
The international bank account number.

``consale_method_account_bic``
"""""""""""""""""""""""""""""""""""""""""
The bank identifier code.

``consale_method_account_bank``
"""""""""""""""""""""""""""""""""""""""""
The bank name.

``consale_recurring_payment_provider``
"""""""""""""""""""""""""""""""""""""""""
When the ``consale_method`` = ``directdebit``, specify one of these values

- ``frst`` If DataDialog is supposed to handle the recurring payment
- ``external`` If the recurring payment is handled by yourself or externally

..
    consale_error_code
    consale_error_msg


Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
