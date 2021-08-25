.. _payment_acquirer:

=========================================
payment.acquirer
=========================================

Contains a list of known payment acquirers, used to identify how a payment was received.

.. note:: Only reading is supported for this model.

Fields
------
- ``id`` ID used as foreign key in other models
- ``name`` The name of the payment acquirer
- ``environment`` Is the acquirer for test or production?
- ``recurring_transactions`` Are recurring transactions supported?
- ``provider`` Who is the payment provider?

..
    do_not_send_status_email
    globally_hidden
    ogonedadi_brand
    ogonedadi_pm
    ogonedadi_userid
    redirect_url_after_form_feedback
    validation
    website_published


Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
