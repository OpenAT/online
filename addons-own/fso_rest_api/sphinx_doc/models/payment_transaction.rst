.. _payment_transaction:

=========================================
payment.transaction
=========================================

Represents an actual payment, including all the payment specific information.


Special fields
--------------

``state``
""""""""""""""""""""
The state of the transaction. Can be either:

- ``done`` The payment was successfully processed
- ``draft`` Payment still in draft
- ``pending`` Payment is in progress. **Use this for direct debit donations processed by DataDialog**
- ``error`` Error during payment
- ``cancel`` Payment was cancelled

``frst_iban``
""""""""""""""""""""
The international bank account number.

.. NOTE:: This is required for direct debit.

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

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
