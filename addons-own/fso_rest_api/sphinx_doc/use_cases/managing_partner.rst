.. _managing_partner:

==================
Managing Partner
==================

Please make sure to read the :ref:`res.partner model documentation <res_partner>` carefully before
you work through the partner management use cases.

Search for partner
------------------

To search for partner we send a ``PATCH`` request to the route ``/res.partner/call/search`` to call the
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

        # Search case insensitive for partners with 'musterman' in it's lastname
        search_domain = [('lastname', 'ilike', 'musterman')]
        response = requests.patch(api_base_url + '/res.partner/call/search',
                                  headers={'accept': 'application/json'},
                                  json={"args": [search_domain]},
                                  auth=auth)

        # Returns list of res.partner ids:
        # print(response.content)
        # >>> b'[1720, 1713, 1719]'

.. tip:: The json dictionary of the requests payload accepts two keywords. Use ``args`` to provide a list of
    positional arguments and ``kwargs`` to provide a dictionary (associative array) for the keyword arguments
    of the function.

Read the partner data
---------------------

To get the data for the found partner in the previous example we send a ``GET`` request to the
route ``/res.partner/{id}``.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 13

        import requests
        from  requests.auth import HTTPBasicAuth


        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Get partner data for partner with the id's 1720, 1713 and 1719
        for partner_id in [1720, 1713, 1719]:
            response = requests.get(api_base_url + '/res.partner/' + str(partner_id), auth=auth)

            print(response.content)

    .. code-tab:: python Example-Response-Content

        {   'active': True,
            'anrede_individuell': '',
            'birthdate_web': '',
            'bpk_forced_birthdate': '',
            'bpk_forced_firstname': '',
            'bpk_forced_lastname': '',
            'bpk_forced_street': '',
            'bpk_forced_zip': '',
            'city': '',
            'company_name_web': '',
            'country_id': False,
            'donation_deduction_optout_web': False,
            'email': '',
            'fax': '',
            'firstname': 'Max',
            'frst_zverzeichnis_id': False,
            'gdpr_accepted': False,
            'gender': '',
            'id': 1720,
            'lastname': 'Mustermann',
            'mobile': '',
            'name_zwei': '',
            'newsletter_web': False,
            'phone': '',
            'street': '',
            'street_number_web': '',
            'title_web': '',
            'zip': ''}
        {   'active': True,
            'anrede_individuell': '',
            'birthdate_web': '',
            'bpk_forced_birthdate': '',
            'bpk_forced_firstname': '',
            'bpk_forced_lastname': '',
            'bpk_forced_street': '',
            'bpk_forced_zip': '',
            'city': '',
            'company_name_web': '',
            'country_id': False,
            'donation_deduction_optout_web': False,
            'email': 'max2@test.com',
            'fax': '',
            'firstname': 'Max',
            'frst_zverzeichnis_id': False,
            'gdpr_accepted': False,
            'gender': '',
            'id': 1713,
            'lastname': 'Mustermann',
            'mobile': '',
            'name_zwei': '',
            'newsletter_web': False,
            'phone': '',
            'street': '',
            'street_number_web': '',
            'title_web': '',
            'zip': ''}
        {   'active': True,
            'anrede_individuell': '',
            'birthdate_web': '',
            'bpk_forced_birthdate': '',
            'bpk_forced_firstname': '',
            'bpk_forced_lastname': '',
            'bpk_forced_street': '',
            'bpk_forced_zip': '',
            'city': '',
            'company_name_web': '',
            'country_id': False,
            'donation_deduction_optout_web': False,
            'email': '',
            'fax': '',
            'firstname': 'Maximilian',
            'frst_zverzeichnis_id': False,
            'gdpr_accepted': False,
            'gender': '',
            'id': 1719,
            'lastname': 'Mustermann',
            'mobile': '',
            'name_zwei': '',
            'newsletter_web': False,
            'phone': '',
            'street': '',
            'street_number_web': '',
            'title_web': '',
            'zip': ''}

Updating partner data
---------------------

To change partner data we send a ``PUT`` request to the route ``/res.partner/{id}`` and provide the
field data as the json payload of the request.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 15-18

        # Fundraising Studio REST API Examples

        import requests
        from  requests.auth import HTTPBasicAuth

        # API Base URL
        api_base_url = "http://demo.local.com/api/v1/frst"

        # Prepare Authorization
        auth = HTTPBasicAuth('demo', 'bb3479ed-2193-47ac-8a41-3122344dd89e')

        # Update partner data
        response = requests.put(api_base_url + '/res.partner/1720',
                                headers={'accept': 'application/json'},
                                json={"street": "Main Street",
                                      "street_number_web": "82",
                                      "newsletter_web": True,
                                      },
                                auth=auth)

        print(response.status_code)
        # >>> 204

.. tip:: You do NOT need to provide all the available fields of the record but just the fields that you want
    change!

Creating a partner
------------------

To create a new partner data we send a ``POST`` request to the route ``/res.partner/{id}`` and provide the
field data as the json payload of the request.

TODO: Code Example

Deleting a partner
------------------

To delete a new partner we send a ``DELETE`` request to the route ``/res.partner/{id}``.

TODO: Code Example

.. attention:: In general you may only be able to delete partners that where created by you! Deletion of other
    partners may fail with an access error.
