.. _searching:

==================
Searching
==================

Searching for records can be done by the ``search`` method. Any available model has a search method.
It can be called by the api via routes with ``.../call/search/...`` in them.

The search method needs at least a :ref:`search_domain` for the current model. Such a search domain consists of
any number of search criteria each made up of three arguments:

``("field_name", "operator", "search_value")``.

.. tip:: If not otherwise stated all search criteria are combined as ``AND``.

.. _search_examples:

Search Basics
-------------

Name search
""""""""""""

To search for a partner where the string "ax" is anywhere in the field ``firstname`` and the lastname is
exactly "Mustermann" we could use a search domain like:

.. code-block::

    [('firstname', 'ilike', 'ax'), ('lastname', '=', 'Mustermann')]

This will find partner like e.g. "Max Mustermann", "Axel Mustermann" and alike.

Combining criteria with ``OR``
""""""""""""""""""""""""""""""""
If we wanted to search for "Mustermann" ``OR`` "Musterfrau" the domain would look like:

.. code-block::

    #               A                                 B                                C
    [('firstname', 'ilike', 'ax'), '|', ('lastname', '=', 'Mustermann'), ('lastname', '=', 'Musterfrau')]

The ``'|'`` operator combines the next two search criteria as ``B OR C`` So the full :ref:`search_domain` reads like
``A AND (B OR C)``. This kind of notation is called `Polish notation <https://en.wikipedia.org/wiki/Polish_notation>`__
and is a mathematical notation in which operators precede their operands, in contrast to the more common infix notation.
This notation may be familiar for you if you had an HP calculator. Mor information about it can be found
`here <https://en.wikipedia.org/wiki/Polish_notation>`__.

Negate an operator
"""""""""""""""""""

Most operators of the search criterias can be negated by an ``!`` or the word ``not``.
E.g. **not equals to** would be ``!=`` and **case insensitive not like** would be ``not ilike``


Searching for related data
""""""""""""""""""""""""""

If you want to search for all partners linked to a country with the name "Österreich" you could directly use
the data of the related record by dot notation:

.. code-block:: python

    search_domain = [('country_id.name', '=', 'Österreich')]

    # Full request
    response = requests.patch('http://demo.local.com/api/v1/frst/res.partner/call/search',
                              headers={'accept': 'application/json'},
                              json={"args": [search_domain]
                                    },
                              auth=auth)


``search`` method options
-------------------------

The search method provides additional keyword arguments for limiting the search result or to realise pagination.

    * ``offset`` (int) -- number of results to ignore (default: none)
    * ``limit`` (int) -- maximum number of records to return (default: all)
    * ``order`` (str) -- sort string
    * ``count`` (bool) -- if True, only counts and returns the number of matching records (default: False)

Example:

.. code-block:: python

    search_domain = [('country_id.name', '=', 'Österreich')]

    # Full request
    response = requests.patch('http://demo.local.com/api/v1/frst/res.partner/call/search',
                              headers={'accept': 'application/json'},
                              json={"args": [search_domain],
                                    "kwargs": {"limit": 100,
                                               "order": "id desc"}
                                    },
                              auth=auth)
