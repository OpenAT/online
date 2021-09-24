.. _products:

=========================================
product.template, product.product
=========================================

These two models represent donation products or physical products and their variants. The template can be seen
as a container for one or more ``product_product`` entries (variants).

**Example 1:**

- ``product.template`` Fight animal cruelty (donation product)

  - ``product.product`` Default entry

.. HINT:: This is the default for donation products.

.. HINT:: The API creates a :ref:`product_product` automatically.
    After creating a :ref:`product_template` you can simply read the ``product_variants_id``
    of the create-response to get values for ``product_id`` in :ref:`sale_order_line`.

**Example 2:**

- ``product.template`` T-Shirt (with 2 sizes, and 2 colors)

  - ``product.product`` Size S Black

  - ``product.product`` Size S White

  - ``product.product`` Size M Black

  - ``product.product`` Size M White

.. WARNING:: Example 2 is for explanation only. Only products with their default variant are currently supported.

.. _product_template:

=========================================
product.template
=========================================

Special fields
--------------

``name``
"""""""""""""""""""""
The name of the donation product or physical product.

``description_sale``
"""""""""""""""""""""
A short description of the donation product or physical product.

``fs_product_type``
"""""""""""""""""""""
The FundraisingStudio type of the donation product or physical product, can be either:

- ``donation`` Donations, Sponsorships. **Use this for donation products.**
- ``product`` Physical products, e.g. event tickets
- ``mediation`` E.g. pet adoptions

``type``
"""""""""""""""""""""
The type of the donation product or physical product, can be either:

- ``service`` Services. **Use this for donation products.**
- ``product`` A stockable, physical product
- ``consu`` A consumable good that is not exactly measured, like paper

``product_variant_ids``
"""""""""""""""""""""""
An ``id`` list of all the associated :ref:`product_product` entries.

.. HINT:: Currently all products should have only their default variant.

``payment_interval_lines_ids``
""""""""""""""""""""""""""""""
The possible payment intervals associated with this donation product or physical product.

When placing a :ref:`sale_order_line`, only intervals that are linked via interval lines
can be used for the ``payment_interval_id``.

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.


.. _product_product:

=========================================
product.product
=========================================

Represents one variant of a donation product or physical product. Each variant is a separate entry,
and multiple variants can reference the same ``product.template``.

**Currently all products can have only a single default variant.**

See example 2 in :ref:`products` for a detailed representation of templates and variants.

Special fields
--------------

``product_tmpl_id``
"""""""""""""""""""""
The foreign key to :ref:`product.template <product_template>`.


Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
