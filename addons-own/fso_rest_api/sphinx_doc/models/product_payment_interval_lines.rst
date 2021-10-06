.. _product_payment_interval_lines:

=========================================
product.payment_interval_lines
=========================================

Each entry in this model designates a possible :ref:`product_payment_interval` for a given
:ref:`product_template`.

**Example:**

A donation for "Fight animal cruelty" should only allow one-time, monthly or annual payments.

- ``product.template`` Donation: Fight animal cruelty

  - ``product.payment_interval_lines`` One time donation (``once-only``)
  - ``product.payment_interval_lines`` Recurring monthly (``monthly``)
  - ``product.payment_interval_lines`` Recurring annually (``annually``)

.. NOTE:: This information is relevant when placing a :ref:`sale_order_line`, because the
    order line checks the possible payment intervals for a given product.

Fields
------
- ``id`` ID used as foreign key in other models
- ``product_id`` The ``id`` of the :ref:`product_template`
- ``payment_interval_id`` The ``id`` of the :ref:`product_payment_interval`

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
