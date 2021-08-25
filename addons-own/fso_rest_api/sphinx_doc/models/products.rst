.. _products:

=========================================
product.template, product.product
=========================================

These two models represent products and its variants. The template can be seen as a container
for one or more ``product_product`` entries (variants).

**Example 1:**

- ``product.template`` Fight animal cruelty (donation)

  - ``product.product`` Empty entry (it has no variants, it is a donation)

.. HINT:: This is the default for donation products.

**Example 2:**

- ``product.template`` T-Shirt (with 2 sizes, and 2 colors)

  - ``product.product`` Size S Black

  - ``product.product`` Size S White

  - ``product.product`` Size M Black

  - ``product.product`` Size M White

.. WARNING:: Example 2 is for explanation only. Only donations (template 1:1 products) are currently supported.

.. _product_template:

=========================================
product.template
=========================================

Special fields
--------------

``name``
"""""""""""""""""""""
The name of the product or the donation.

``fs_product_type``
"""""""""""""""""""""
The FundraisingStudio type of the product, can be either:

- ``donation`` Donations, Sponsorships
- ``product`` Physical products, e.g. event tickets
- ``mediation`` E.g. pet adoptions


``type``
"""""""""""""""""""""
The type of the product, can be either:

- ``service`` Services. **Use this for donations!**
- ``product`` A stockable physical product
- ``consu`` A consumable good that is not exactly measured, like paper


..
    Commented for future use:

    product_page_template
    active
    description_sale
    website_url
    list_price
    price_donate
    price_donate_min
    website_published
    website_published_start
    website_published_end
    website_visible
    default_code


Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.


.. _product_product:

=========================================
product.product
=========================================

Represents one variant of a product. Each variant is a separate entry, and multiple variants can
reference the same :ref:`products`.

**Most donation products will only need an empty entry of this model, in order to generate an id, to use
as a foreign key for other models.**

See example 2 in :ref:`products` for a detailed representation of templates and variants.


Special fields
--------------

``product_tmpl_id``
"""""""""""""""""""""
The foreign key to :ref:`products`.


Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
