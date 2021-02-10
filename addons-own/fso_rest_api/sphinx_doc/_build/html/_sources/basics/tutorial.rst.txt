.. _basic_tutorial:

===========================================
Tutorial
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
* Database-Name and Api-User-Token
    e.g.: demo, 2c8628e4-6bd6-4c90-a6e7-8872afde8f39

Swagger UI
----------
An easy starting point to explore the openapi specification with all the routes and available commands is through
the provided Swagger UI. Just open the provided Fundraising Studio Swagger-UI-API-URL and you will get to the
web interface with the correct openapi json specification already loaded.

.. image:: /basics/images/swagger_ui.png
    :align: left

1. Authorize yourself
"""""""""""""""""""""
Before you try any of the routes (functions) of the api you have to provide your credentials by pressing the button
:guilabel:`Authorize` in the upper right corner and entering your ``database-name`` and ``api-user-token``.

.. image:: /basics/images/swagger_ui_access.png
    :align: left

.. attention:: You do NOT need to provide the login (name) of you api user but the **name of the database**!
    The database name may be something like ``dadi``, ``demo`` or alike. The login of the user is already
    "baked" into the api token.

If you look closely you will see that the lock is now closed on all routes showing you that any further request will be
done with the provided credentials:

.. image:: /basics/images/swagger_ui_authorized.png
    :align: left

.. WARNING:: When not authenticated correctly the api may return 200 instead of designed 401 with a message
    like this:

    .. code-block::

        File "/opt/odoo/vendor/it-projects-llc/sync-addons/openapi/controllers/pinguin.py", line 152, in authenticate_token_for_user
            raise werkzeug.exceptions.HTTPException(response=error_response(*CODE__no_user_auth))
        HTTPException: ??? Unknown Error: None

2. Try the routes
"""""""""""""""""

Now that we are authorized we can try out all the provided routes in the openapi file. Let's try to load some data
from a person with the id ``1``.

.. image:: /basics/images/swagger_ui_try.png
    :align: left

To do this press the :guilabel:`Try it out` button and enter ``1`` in the parameter ``id``. Then press the execute
button to send the command. Swagger UI will show you the request made with curl as well as the answer code and content
returned by the server. In our simple example case we get the fields ``firstname`` and ``lastname`` from the partner

.. image:: /basics/images/swagger_ui_get_partner_1.png
    :align: left

The http request is done by swagger ui with curl but you can use any programming language that is able to handle
http requests to do the same!

.. tabs::

    .. code-tab:: bash

        curl -X GET "http://demo.local.com/api/v1/frst/res.partner/1" -H  "accept: application/json" -H  "authorization: Basic YWRtaW46MmM4NjI4ZTQtNmJkNi00YzkwLWE2ZTctODg3MmFmZGU4ZjM5"

    .. code-tab:: python

        # https://github.com/Yelp/bravado
        from bravado.requests_client import RequestsClient
        from bravado.client import SwaggerClient

        integration_domain = "demo.local.com"
        integration_db_name = "demo"
        integration_api_token = "your-integration-api-token"
        integration_spec_url = "https://%s/api/v1/frst/swagger.json?token=%s&db=%s" % (integration_domain, integration_api_token, integration_db_name)

        api_user_token = "your-api-users-token"

        # Create http-client
        http_client = RequestsClient()

        # Add authorization information to the http-client
        http_client.set_basic_auth(integration_domain, integration_db_name, api_user_token)

        # Create bravado client based on the openapi specification file
        bravado_swagger_client = SwaggerClient.from_url(
            integration_spec_url,
            http_client=http_client
        )

        # TODO: Remove below code with a simple "get partner with id 1" example!

        result = bravado_swagger_client.res_partner.callMethodForResPartnerModel(
            method_name="search",
            body={
                'args': [[('email', '=', 'sync@it-projects.info')]]
            }
        ).response().incoming_response.json()

        partner_id = result and result[0]

        if not partner_id:
            result = bravado_swagger_client.res_partner.addResPartner(body={
                "name": "OpenAPI Support",
                "email": "sync@it-projects.info"
            }).response().result
            partner_id = result.id

        bravado_swagger_client.res_partner.callMethodForResPartnerSingleRecord(
          id=partner_id,
          method_name="message_post",
          body={
            "kwargs": {
              "body": "The Openapi module works in Python! Thank you!",
              "partner_ids": [partner_id]
            }
          }
        ).response()



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

Methods can be called by any route with ``/call/{method_name}`` in it. In this example we will use ``/call/search`` to
search non case sensitive for persons with ``max`` in it's firstname:

.. tabs::

    .. code-tab:: bash

        TODO: Apples are green, or sometimes red.

    .. code-tab:: python

        TODO: Pears are green.

