.. _res_country:

=========================================
res.country
=========================================

Contains a list of known countries in the system.

.. note:: Only reading is supported for this model.

Fields
------
- ``id`` ID used as foreign key in other models
- ``name`` The name of the country
- ``code`` The 2 character ISO code

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
