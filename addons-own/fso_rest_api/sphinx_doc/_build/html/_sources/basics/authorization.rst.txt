.. _authorization:

==================================
Authorization
==================================

To authorize at the Fundraising Studio REST API a HTTP-Basic authorization is enough. You need the ``database-name`` and
an ``api-user-token`` to authorize your session or request.

Example:

.. code-block::

        import requests
        from  requests.auth import HTTPBasicAuth

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Read the data of res.partner with id "1234"
        response = requests.get('http://demo.local.com/api/v1/frst/res.partner/1234', auth=auth)


.. attention:: If your request is not authorized correctly you may get a different error status code instead
    of the expected error status code ``401``!

    This is due to security restrictions that may block the request under certain circumstances
    long before it even comes to the REST API.

