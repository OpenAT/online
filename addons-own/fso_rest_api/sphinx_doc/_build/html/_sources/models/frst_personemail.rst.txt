.. _frst_personemail:

==================
frst.personemail
==================

Records of this model represent an email address of a partner.

All email records of one partner must have a unique value for the email field but there may be another
frst.personemail record with the same email address for an other partner!

Required fields
---------------
The minimum required fields for a new ``frst.personemail`` record are ``email`` and ``partner_id``.

.. attention::

    email addresses (:ref:`frst_personemail` records) may also be created or (re)activated by changing the
    :ref:`res_partner` field ``email``!

Non obvious behaviours
----------------------

.. _frst_personemail_nob_state:

``state``
"""""""""""""""""""""
Valid states of an email address record are:

.. code-block::

    'active'           # The email is in use
    'inactive'         # The email is disabled and must not be used!

.. attention:: Make sure to use only ``state=active`` email addresses unless your really know what you are doing!

``last_email_update``
"""""""""""""""""""""

Basically this is the order/sequence of the email address records of a partner. The
latest email address record with a valid e-mail address will be the current main email address if
``forced_main_address`` is not set in any other record.

``forced_main_address``
"""""""""""""""""""""""

If set this will be the new main email adress of the linked partner. The ``forced_mail_address`` will be removed
from any other email address record linked to this partner in favour of the last one. The email of the forced
main email address record will show up in the :ref:`res_partner` field ``email``.

``main_address``
""""""""""""""""

This field is computed based on ``last_email_update``, ``main_address`` and ``state`` and therefore can NOT be set!
It indicates the current main e-mail address record of the partner. The email of this record will be copied to the
:ref:`res_partner` field ``email``.

``gueltig_von``, ``gueltig_bis``
""""""""""""""""""""""""""""""""

The values of this fields are calculated automatically. Some dates may even have a special meaning. Therefore it is
strongly advised NOT to set or change the values of those fields by the api except you really know what you are
doing!

.. warning:: Do NOT set or change these fields by the api unless you really know what you are doing!
