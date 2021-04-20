.. _email_subscriptions:

====================
Email Subscriptions
====================

Search for email group folders
------------------------------
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
