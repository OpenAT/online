.. _email_subscriptions:

====================
Email Subscriptions
====================

Search for email group folders
------------------------------

.. attention::
    This should not be done from web forms directly. Implement this in your management backend and
    simply cache the data locally.

To search for email group folders we send a ``PATCH`` request to the route ``/frst.zgruppe/call/search`` to call the
``search`` method and we provide a :ref:`search domain <search_domain>` as the first positional argument
of the search method to specify our search conditions.

The example searches for group folders of ``tabellentyp_id`` with value ``100110``, returning all folders that
contain groups that are applicable for email addresses.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 14-18, 29-32

        # Fundraising Studio REST API Examples

        import json
        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Search for group folders that are applicable for emails (tabellentyp_id = 100110)
        search_domain = [('tabellentyp_id', '=', 100110)]
        response = requests.patch(api_base_url + '/frst.zgruppe/call/search',
                                  headers={'accept': 'application/json'},
                                  json={"args": [search_domain]},
                                  auth=auth)

        # Returns list of frst.zgruppe ids:
        # print(response.content)
        # >>> b'[30150, 30200]'

        # Parse the JSON response into an object
        group_id_list = json.loads(response.content)

        # Cycle all IDs and request the full object
        for group_id in group_id_list:
            # Request the group with the current ID
            response = requests.get(api_base_url + '/frst.zgruppe/%s' % group_id,
                                    headers={'accept': 'application/json'},
                                    auth=auth)

            # Parse the response into an object
            group = json.loads(response.content)

            # Print the name of the group
            print("%s: %s" % (group["id"], group["gruppe_lang"]))

        # The loop prints the group folders, for example:
        # >>> 30150: Herkunft
        # >>> 30200: Newsletter

Search for email groups
-----------------------

.. attention::
    This should not be done from web forms directly. Implement this in your management backend and
    simply cache the data locally.

Once you have picked a desired group folder, for example ``30200`` (``Newsletter``), you can search for
actual groups inside the group folder.

To search for email groups we send a ``PATCH`` request to the route ``/frst.zgruppedetail/call/search`` to call the
``search`` method and we provide a :ref:`search domain <search_domain>` as the first positional argument
of the search method to specify our search conditions.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 14-18, 29-32

        # Fundraising Studio REST API Examples

        import json
        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Search for groups in group folder id 30200
        search_domain = [('zgruppe_id', '=', 30200)]
        response = requests.patch(api_base_url + '/frst.zgruppedetail/call/search',
                                  headers={'accept': 'application/json'},
                                  json={"args": [search_domain]},
                                  auth=auth)

        # Returns list of frst.zgruppe ids:
        # print(response.content)
        # >>> b'[30104, 30208, 30221]'

        # Parse the JSON response into an object
        group_id_list = json.loads(response.content)

        # Cycle all IDs and request the full object
        for group_id in group_id_list:
            # Request the group with the current ID
            response = requests.get(api_base_url + '/frst.zgruppedetail/%s' % group_id,
                                    headers={'accept': 'application/json'},
                                    auth=auth)

            # Parse the response into an object
            group = json.loads(response.content)

            # Print the name of the group
            print("%s: %s" % (group["id"], group["gruppe_lang"]))

        # The loop prints the group folders, for example:
        # >>> 30104: Newsletter
        # >>> 30208: Kinder-Newsletter
        # >>> 30221: Notfall-Newsletter


Subsribe to a newsletter
------------------------

Assuming a simple web form that captures **first name**, **last name** and **email**, subscribing to a newsletter
consists of two ``POST`` requests:
    1) Create ``res.partner`` (be sure to include ``email``)
    2) Create ``frst.personemailgruppe`` using the IDs from the first request

See `Search for email groups`_ on how to obtain possible values for ``zgruppedetail_id``. The example
just uses a hard coded value.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 18-22, 36-40

        import json
        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Prepare partner data, including E-Mail
        partner_data = {
            "firstname": "Maxime",
            "lastname": "Muster",
            "email": "maxime.muster@datadialog.net"
        }

        # Create the partner
        response = requests.post(api_base_url + '/res.partner',
                                headers={'accept': 'application/json'},
                                auth=auth,
                                json=partner_data)

        # Parse the JSON response so we can fetch ID values
        created_partner = json.loads(response.content)
        partner_id = created_partner["id"]
        personemail_id = created_partner["main_personemail_id"]

        # Prepare subscription data
        subscription_data = {
            "partner_id": partner_id,
            "frst_personemail_id": personemail_id,
            "zgruppedetail_id": 30221 # Notfall-Newsletter
        }

        # Create the subscription by creating ``frst.personemailgruppe``
        response = requests.post(api_base_url + '/frst.personemailgruppe',
                                headers={'accept': 'application/json'},
                                auth=auth,
                                json=subscription_data)

        subscription = json.loads(response.content)
        print("Subscription state: %s" % subscription["state"])
        # Example 1: >>> Subscription state: approval_pending
        # Example 2: >>> Subscription state: subscribed
