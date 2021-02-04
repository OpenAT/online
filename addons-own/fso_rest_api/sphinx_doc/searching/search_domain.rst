.. _search_domain:

==================
Search Domain
==================

domain criterion
----------------
A domain is a list of criteria, each criterion being a triple (either a
``list`` or a ``tuple``) of

``(field_name, operator, value)``

------------------------------------------------------------------------------

``field_name`` (``str``)
****************************
    a field name of the current model, or a relationship traversal through
    a :class:`~openerp.fields.Many2one` using dot-notation e.g. ``'street'``
    or ``'partner_id.country'``

``operator`` (``str``)
****************************
    an operator used to compare the ``field_name`` with the ``value``. Valid
    operators are:

    ``=``
        equals to
    ``!=``
        not equals to
    ``>``
        greater than
    ``>=``
        greater than or equal to
    ``<``
        less than
    ``<=``
        less than or equal to
    ``=?``
        unset or equals to (returns true if ``value`` is either ``None`` or
        ``False``, otherwise behaves like ``=``)
    ``=like``
        matches ``field_name`` against the ``value`` pattern. An underscore
        ``_`` in the pattern stands for (matches) any single character; a
        percent sign ``%`` matches any string of zero or more characters.
    ``like``
        matches ``field_name`` against the ``%value%`` pattern. Similar to
        ``=like`` but wraps ``value`` with '%' before matching
    ``not like``
        doesn't match against the ``%value%`` pattern
    ``ilike``
        case insensitive ``like``
    ``not ilike``
        case insensitive ``not like``
    ``=ilike``
        case insensitive ``=like``
    ``in``
        is equal to any of the items from ``value``, ``value`` should be a
        list of items
    ``not in``
        is unequal to all of the items from ``value``
    ``child_of``
        is a child (descendant) of a ``value`` record.

        Takes the semantics of the model into account (i.e following the
        relationship field named by
        :attr:`~openerp.models.Model._parent_name`).

``value``
****************************
    variable type, must be comparable (through ``operator``) to the named
    field

Logical Operators
-----------------

Domain criteria can be combined using logical operators in *prefix* form:

``'&'``
    logical *AND*, default operation to combine criteria following one
    another. Arity 2 (uses the next 2 criteria or combinations).
``'|'``
    logical *OR*, arity 2.
``'!'``
    logical *NOT*, arity 1.

    .. tip:: Mostly to negate combinations of criteria
        :class: aphorism

        Individual criterion generally have a negative form (e.g. ``=`` ->
        ``!=``, ``<`` -> ``>=``) which is simpler than negating the positive.

.. admonition:: Example

    To search for partners named *ABC*, from belgium or germany, whose language
    is not english::

        [('name','=','ABC'),
         ('language.code','!=','en_US'),
         '|',('country_id.code','=','be'),
             ('country_id.code','=','de')]

    This domain is interpreted as:

    .. code-block:: text

            (name is 'ABC')
        AND (language is NOT english)
        AND (country is Belgium OR Germany)

