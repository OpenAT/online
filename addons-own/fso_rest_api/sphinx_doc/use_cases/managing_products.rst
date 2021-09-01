.. _managing_products:

===============================
Managing products
===============================

Search for products
--------------------------------
To search for products we send a ``PATCH`` request to the route ``/product.template/call/search`` to call the
``search`` method and we provide a :ref:`search domain <search_domain>` as the first positional argument
of the search method to specify our search conditions.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 14-17

        # Fundraising Studio REST API Examples

        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Search case insensitive for products with 'animal' in the name
        search_domain = [('name', 'ilike', 'animal')]
        response = requests.patch(api_base_url + '/product.template/call/search',
                                  headers={'accept': 'application/json'},
                                  json={"args": [search_domain]},
                                  auth=auth)

        # Returns list of product.template ids:
        # print(response.content)
        # >>> b'[33, 37]'

Read the product data
---------------------------------
To get the data for the found ``product.template`` in the previous example we send a ``GET`` request to the
route ``/product.template/{id}``.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 12

        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Get product data for the id 37
        template_id = 37
        response = requests.get(api_base_url + '/product.template/' + str(template_id), auth=auth)

        print(response.content)

    .. code-tab:: python Example-Response-Content

        {
            "id": 37,
            "create_uid": 1,
            "create_date": "2021-06-04 09:19:59",
            "write_uid": 1,
            "write_date": "2021-06-23 12:35:45",
            "name": "Fight animal cruelty",
            "fs_product_type": "donation",
            "product_page_template": "website_sale_donate.ppt_donate",
            "type": "service",
            "active": true,
            "description_sale": "",
            "website_url": "/shop/product/37",
            "list_price": 25.0,
            "price_donate": true,
            "price_donate_min": 8,
            "website_published": true,
            "website_published_start": "",
            "website_published_end": "",
            "website_visible": true,
            "default_code": "",
            "product_variant_ids": [4],
            "payment_interval_lines_ids": [1]
        }

Updating product data
---------------------------------
To change product data we send a ``PUT`` request to the route ``/product.template/{id}`` and provide the
field data as the json payload of the request.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 15-17

        # Fundraising Studio REST API Examples

        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Update product.template data
        response = requests.put(api_base_url + '/product.template/37',
                                headers={'accept': 'application/json'},
                                json={"list_price": 35.0,
                                      "price_donate_min": 10.0,
                                      },
                                auth=auth)

        print(response.status_code)
        # >>> 204

.. tip:: You do NOT need to provide all the available fields of the record but just the fields that you want
    change!

.. important:: An API user can **only modify its own records**. Records of other users are read-only.

Creating a product
------------------------------

To create a new donation or product we send a ``POST`` request to the route ``/product.template`` and provide the
field data as the json payload of the request.

The example below also supplies values for the model :ref:`product_payment_interval_lines`.

.. tabs::

    .. code-tab:: python

        # Fundraising Studio REST API Examples

        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Manually pick IDs from the model product.payment_interval,
        # alternatively use search to query IDs directly.
        interval_once_only = 6
        interval_monthly = 7

        # List of tuples. Each tuple has the format: (0, _, data)
        # and represents a list operation.
        #    0 = add record to list
        #    second parameter can be anything
        #    data = dictionary with single key: payment_interval_id
        interval_lines = [
            (0, False, { 'payment_interval_id': interval_once_only }),
            (0, False, { 'payment_interval_id': interval_monthly }),
        ]

        # Create a minimal donation product, including interval lines.
        # This avoids using a separate request to populate payment intervals
        template_data = {
            'name': 'Support young whelps',
            'description_sale': 'Support rescuing and raising young whelps.',
            'type': 'service',
            'fs_product_type': 'donation',
            'payment_interval_lines_ids': interval_lines
        }
        response = requests.post(api_base_url + '/product.template', auth=auth, json=template_data)

    .. code-tab:: python Example-Response-Content
        :emphasize-lines: 22

        {
            "id": 39,
            "create_uid": 8,
            "create_date": "2021-09-01 10:13:07",
            "write_uid": 8,
            "write_date": "2021-09-01 10:13:07",
            "name": "Support young whelps",
            "fs_product_type": "donation",
            "product_page_template": "website_sale_donate.ppt_donate",
            "type": "service",
            "active": true,
            "description_sale": "Support rescuing and raising young whelps.",
            "website_url": "/shop/product/7",
            "list_price": 1.0,
            "price_donate": true,
            "price_donate_min": 0,
            "website_published": false,
            "website_published_start": "",
            "website_published_end": "",
            "website_visible": false,
            "default_code": "",
            "product_variant_ids": [10],
            "payment_interval_lines_ids": [15, 16]
        }


.. hint:: Note that a :ref:`product_product` is created automatically with the ``product.template``.

.. hint:: You can parse the response of the create command to obtain the created ``product.product`` IDs via
    the field ``product_variants_ids``.

.. _Odoo_ORM_Documentation: https://www.odoo.com/documentation/8.0/reference/orm.html#openerp-models-relationals-format

.. hint:: The possible payment intervals are directly provided via Odoo list operations. The example should be
    sufficient for most cases, but you can see the Odoo_ORM_Documentation_ for all the details.

Deleting a product
------------------------------
Products cannot be deleted via the API.
