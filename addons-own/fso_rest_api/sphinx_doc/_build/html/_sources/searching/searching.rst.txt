.. _searching:

==================
Searching
==================

To search for records can be done by the search method. Any available model has a search method.
It can be called by the api via routes with ``.../call/search/...`` in them.

The search method needs at least a :ref:`search_domain` for the current model. Such a search domain consists of
any number of search criteria each made up of three arguments:

``("field_name", "operator", "search_value")``.

.. tip:: If not otherwise stated all search criteria are combined as ``AND``.

.. _search_examples:

Search Examples
---------------

Partner search
"""""""""""""""

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
``A AND (B OR C)``

Negate an operator
"""""""""""""""""""

Most operators of the search criterias can be negated by an ``!`` or the word ``not``.
E.g. **not equals to** would be ``!=`` and **case insensitive not like** would be ``not ilike``


Searching for related data
""""""""""""""""""""""""""

TODO

