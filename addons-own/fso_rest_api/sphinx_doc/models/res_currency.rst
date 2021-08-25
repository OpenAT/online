.. _res_currency:

=========================================
res.currency
=========================================

Contains a list of known currencies in the system.

Fields
------
- ``id`` ID used as foreign key in other models
- ``name`` The 3 character ISO code
- ``symbol`` The symbol used by the currency, e.g. ``€`` for currency ``EUR``

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
