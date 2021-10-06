.. _sale_orders:

=========================================
sale.order, sale.order.line
=========================================

These two models represent orders or donations and and order lines. An order can contain multiple order lines,
and order lines reference products (:ref:`product_product`).

**Example:**

- ``sale.order`` SO1

  - ``sale.order.line`` Donation: EUR 30 - "Fight animal cruelty"

  - ``sale.order.line`` Ticket: EUR 10 - "Information event"


.. _sale_order:

=========================================
sale.order
=========================================

The model representing the order itself. It holds order identifiers and order totals etc.

Special fields
--------------

``name``
"""""""""""""""""""""
The order name. Use a unique identifier for orders. Ideally, use a **prefix unique for your
organisation**, followed by a **continuous number**.

For example ``ORG4711``.

``state``
"""""""""""""""""""""
The state of the order. Can be one of these values:

- ``done`` The order is completed
- ``draft`` Draft quotation
- ``sent`` Quotiont was sent
- ``cancel`` The order was cancelled
- ``waiting_date`` The order awaits a specific date
- ``progress`` The order is in progress
- ``manual`` Order was manually approved. **Use this for donations.**
- ``shipping_except`` Shipping error
- ``invoice_except`` Invoicing error

``date_order``
"""""""""""""""""""""
The date and time when the order was placed.

``amount_total``
"""""""""""""""""""""
The total monetary sum of all order lines.

``partner_id``
"""""""""""""""""""""
The foreign key to the :ref:`res_partner`. If the order or donation is a gift, this is the
partner **ordering/paying**.

``giftee_partner_id``
"""""""""""""""""""""
If the order or donation is a gift, this is the foreign key of the :ref:`res_partner` **receiving the gift**.

``payment_tx_id``
"""""""""""""""""""""
The foreign key of the :ref:`payment_transaction`.

``payment_acquirer_id``
"""""""""""""""""""""""
The foreign key of the :ref:`payment_acquirer`.

.. important:: Use `External Payment (Connector Sale)` if

    - You are processing payments yourself
    - You send a direct debit order, to be processed by DataDialog

``order_line``
"""""""""""""""""""""""
The list of all associated :ref:`sale_order_line` entries.

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.


.. _sale_order_line:

=========================================
sale.order.line
=========================================

Represents an order line or order item. It references a :ref:`product_product`, holds information
like price/amount, origin, etc.


Special fields
--------------

``name``
"""""""""""""""""""""
Free text. The name or description for the order line. For example, you could use
the name of the donation product or physical product here.

``state``
"""""""""""""""""""""
State of the order line. Should correspond to the :ref:`sale_order`.

- ``done`` The order line is completed.
- ``cancelled`` The related order was cancelled
- ``draft`` The related order is in draft mode
- ``confirmed`` The sale order is completed. **Use this for donations.**
- ``exception`` Error

``order_id``
"""""""""""""""""""""
The foreign key of the :ref:`sale_order`.

``product_id``
"""""""""""""""""""""
The foreign key of the :ref:`product_product`.

``fs_origin``
"""""""""""""""""""""
Free text. Ideally, this is the website URL on which the order was placed.

``price_unit``
"""""""""""""""""""""
The donation amount or the price of a single product unit.

``product_uos_qty``
"""""""""""""""""""""
Quantity of the donation or product.

- For donations, the quantity should be 1
- For products, set the actual quantity

``price_donate``
"""""""""""""""""""""
The donation amount or the sum of all the product units (``price_unit`` x ``product_uos_qty``).

``payment_interval_id``
"""""""""""""""""""""""
The foreign key to the interval (:ref:`product_payment_interval`) of the recurring donation.

- For donations, the interval can be anything that ``product.template`` allows.
- For products, use the ``id`` for the interval ``once-only``.

``zgruppedetail_ids``
"""""""""""""""""""""
A list of foreign keys to :ref:`frst_zgruppedetail`. For donations, use this to specify the
sponsorship type and to select a specific project, person, or animal.

.. HINT:: Consult DataDialog for correct combinations.

..
    Commented: in case sill needed
    payment_interval_id
    price_unit
    product_uos_qty
    fs_product_type


Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
