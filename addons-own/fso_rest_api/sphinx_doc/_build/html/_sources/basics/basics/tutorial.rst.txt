.. _basic_tutorial:

===========================================
Basics Tutorial
===========================================

This tutorial will give you a glimpse on every important part of the Fundraising Studio Rest Api. At this point we
expect you to have access to at least a test environment and that you have a user and an api-key to
authenticate yourself at the system. If you miss any of those things please get in contact with our support at
`support@datadialog.net`

Prerequisites
-------------

* URL with api-token to download the openapi specification json files
    e.g.: http://demo.local.com/api/v1/frst/swagger.json?token=...
* URL to the Swagger UI to explore and test the API
    e.g.: http://demo.local.com/swagger-ui/index.html?swagger_spec_url=...
* API-User and Api-User-Token
    e.g.: demo_api_user, 2c8628e4-6bd6-4c90-a6e7-8872afde8f39

Swagger UI
----------
An easy starting point to explore the openapi specification with all the routes and available commands is through
the provided Swagger UI. Just open the provided Fundraising Studio Swagger-UI-API-URL and you will get to the
web interface with the correct openapi json specification already loaded.

.. image:: /basics/basics/images/swagger_ui.png
    :align: left

1. Authorize yourself
"""""""""""""""""""""
Before you try any of the routes (functions) of the api you have to Authorize by pressing the button in the upper
right corner and entering your api-user and api-user-token.

.. image:: /basics/basics/images/swagger_ui_access.png
    :align: left

If you look closely you will see that the lock is now closed on all routes showing you that any further request will be
done with the provided credentials.

.. image:: /basics/basics/images/swagger_ui_authorized.png
    :align: left

2. Try the routes
"""""""""""""""""

Now that we are authorized we can try out all the provided routes in the openapi file. Let's try to load some date
from a person with the id "1".

.. image:: /basics/basics/images/swagger_ui_try.png
    :align: left

To do this press the try button and enter "1" in the parameter "id". Then press the execute button to send the command.
Swagger UI will show you the request made with curl as well as the answer code and content returned by the server.
In our case we get the fields firstname and lastname from the partner

.. image:: /basics/basics/images/swagger_ui_get_partner_1.png
    :align: left

The request is done with curl but you can use any programming language that is able to handle http requests to do the
same!

.. tabs::

    .. code-tab:: bash

        curl -X GET "http://demo.local.com/api/v1/frst/res.partner/1" -H  "accept: application/json" -H  "authorization: Basic YWRtaW46MmM4NjI4ZTQtNmJkNi00YzkwLWE2ZTctODg3MmFmZGU4ZjM5"

    .. code-tab:: python

        # Todo (show it with the bravado client)


Response:

.. code-block::

    # Response Body
    {
        "firstname": "",
        "lastname": "YourCompany"
    }

    # Response Headers
    connection: keep-alive
    content-encoding: gzip
    content-type: application/json; charset=utf-8
    date: Thu,21 Jan 2021 14:41:31 GMT
    server: nginx/1.19.6
    transfer-encoding: chunked

Calling Methods
---------------

Methods can be called by any route with /call/{method_name} in it. In this example we will use /call/search to search
for persons.

.. tabs::

    .. tab:: curl

        Apples are green, or sometimes red.

    .. tab:: python

        Pears are green.
