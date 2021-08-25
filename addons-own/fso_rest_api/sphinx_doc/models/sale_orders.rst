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

- ``done`` The order is completed. **Use this for donations.**
- ``draft`` Draft quotation
- ``sent`` Quotiont was sent
- ``cancel`` The order was cancelled
- ``waiting_date`` The order awaits a specific date
- ``progress`` The order is in progress
- ``manual`` Order was manually approved
- ``shipping_except`` Shipping error
- ``invoice_except`` Invoicing error

``date_order``
"""""""""""""""""""""
The date and time the order was placed.

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

``state``
"""""""""""""""""""""
State of the order line. Should correspond to the :ref:`sale_order`.

- ``done`` The order line is completed. **Use this for donations.**
- ``cancelled`` The related order was cancelled
- ``draft`` The related order is in draft mode
- ``confirmed`` The sale order is completed
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

``price_donate``
"""""""""""""""""""""
The product price or donation amount for this order line.

``zgruppedetail_ids``
"""""""""""""""""""""
A list of foreign keys to :ref:`frst_zgruppedetail`. For donations, use this to specify
sponsorship for a specific project, person, or animal.

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
