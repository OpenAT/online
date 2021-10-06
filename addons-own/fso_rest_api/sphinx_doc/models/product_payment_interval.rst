.. _product_payment_interval:

=========================================
product.payment_interval
=========================================

Contains a list of known recurring payment intervals in the system.

.. note:: Only reading is supported for this model.

Fields
------
- ``id`` ID used as foreign key in other models
- ``name`` The name of the interval

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
