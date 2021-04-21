.. _email_subscriptions:

====================
Email Subscriptions
====================

Overview
--------
Relevant models:
    - ``frst.zgruppe``: group folder, consider it like a category. Only type **email** (``tabellentyp_id = 100110``)
      is relevant in this section. It contains multiple groups. See :ref:`frst_groups` for details.
    - ``frst.zgruppedetail``: actual email group or list. A group belongs to exactly one ``frst.zgruppe``.
    - ``res.partner``: person, it contains the main email address and foreign key
    - ``frst.personemailgruppe``: subscription or assignment of an email to a group

.. note::
    Groups are not limited to newsletter groups. They can also be qualifications or classifications used in statistics.
    In this section however, the focus is on newsletter groups.

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


Create email groups
-------------------

.. attention::
    Implement this in your management backend and simply cache the data locally.

You first need the ID of a group folder (``frst.zgruppe``) with ``tabellentyp_id`` of ``100110``.
See `Search for email group folders`_ on how to obtain possible values.

.. note::
    You can only create ``frst.zgruppedetail``. Group folders (``frst.zgruppe``) are read only.

Once you have the desired ``frst.zgruppe`` ID, send a ``POST`` request for the model ``frst.zgruppedetail``
with the desired values.

Use the ``bestaetigung_*`` fields to specify how the confirmation is handled. If you handle confirmation
yourself, you can use ``bestaetigung_erforderlich = False``. If you need **Fundraising Studio** to
handle double opt in, use ``True``, and specify the confirmation type via the ``bestaetigung_typ`` field.

.. note::
    If ``bestaetigung_erforderlich = True``, The ID value for ``bestaetigung_email`` must be
    requested from the organisation or DataDialog. It is not currently queryable by the API.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 22-26

        import json
        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        groupdetail_data = {
            "zgruppe_id": 30200,                        # Newsletter
            "geltungsbereich": "local",                 # fixed
            "gui_anzeigen": True,                       # fixed
            "gruppe_lang": "Special Newsletter Topic",  # Actual newsletter name
            "gruppe_kurz": "Special Newsletter Topic",  # Same as "gruppe_lang"
            "bestaetigung_erforderlich": True,          # True, if confirmation is required for this newsletter
            "bestaetigung_typ": "doubleoptin",          # Confirmation type DOI email
            "bestaetigung_email": 33                    # Confirmation email template ID
        }

        # Create the new newsletter group
        response = requests.post(api_base_url + '/frst.zgruppedetail',
                                  headers={'accept': 'application/json'},
                                  auth=auth,
                                  json=groupdetail_data)

        groupdetail = json.loads(response.content)

        print("Created new newsletter ID %s: %s" % (groupdetail["id"], groupdetail["gruppe_lang"]))


Subscribe to a newsletter
-------------------------

Assuming a simple web form that captures **first name**, **last name** and **email**, subscribing to a newsletter
consists of two ``POST`` requests:

1) Create ``res.partner`` (be sure to include ``email``)
2) Create ``frst.personemailgruppe`` using the IDs from the first request

See `Search for email groups`_ on how to obtain possible values for ``zgruppedetail_id``. The example
just uses a hard coded value.

.. note::
    The resulting subscription state depends on the referenced ``frst.zgruppedetail``.
    For example, if double opt in is enabled for the group, the subscription state would
    be ``approval_pending`` instead of ``subscribed``. Confirmation would finally result
    in the sate ``approved``.

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

Unsubscribe from a newsletter
-----------------------------
Four requests are required to unsubscribe:

1) Find partner via email address
2) Read partner data
3) Search for subscriptions via ``main_personemail_id`` from partner data
4) Call ``deactivate`` and supply all subscription IDs in a single request

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 13-18, 26-29, 34-39, 46-51

        import json
        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        email = "maxime.muster@datadialog.net"

        # Search for partners with the given email
        search_domain = [('email', '=ilike', email)]
        response = requests.patch(api_base_url + '/res.partner/call/search',
                                    headers={'accept': 'application/json'},
                                    json={"args": [search_domain]},
                                    auth=auth)

        partner_id_list = json.loads(response.content)
        partner_id = partner_id_list[0] if partner_id_list else None

        if not partner_id:
            print("No partner found.")
        else:
            # Read partner data to obtain main email address ID
            response = requests.get(api_base_url + '/res.partner/%s' % partner_id,
                                        headers={'accept': 'application/json'},
                                        auth=auth)

            partner = json.loads(response.content)
            email_id = partner["main_personemail_id"]

            # Search subscriptions for the given email ID
            search_domain = [('frst_personemail_id', '=', email_id)]
            response = requests.patch(api_base_url + '/frst.personemailgruppe/call/search',
                                        headers={'accept': 'application/json'},
                                        json={"args": [search_domain]},
                                        auth=auth)

            personemailgroup_id_list = map(str, json.loads(response.content))

            if not personemailgroup_id_list:
                print("No subscription found.")
            else:
                # Deactivate all subscriptions in a single request
                deactivate_data = {} # Use empty dict!
                response = requests.patch(api_base_url + '/frst.personemailgruppe/call/deactivate/%s' % ",".join(personemailgroup_id_list),
                                            headers={'accept': 'application/json'},
                                            json=deactivate_data,
                                            auth=auth)
                # print(response.content) # Empty content if successful
