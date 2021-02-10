.. _frst_group_subscriptions:

=========================================
frst.persongruppe, frst.personemailgruppe
=========================================

Represent the assignment of a person or an email to a matching group.

These assignments are referred to as *group subscriptions*.

.. note::
    Subscriptions can be positive and negative. See steuerung_bit_
    for details.

Common fields
-------------
The following fields are the same for both models.

``state``
"""""""""""""""""""""""""""""
Computed field. The current state of the subscription. It can be one of the
following values:

    - ``approval_pending`` waiting for approval
    - ``subscribed`` subscribed but not approved (e.g. legacy data)
    - ``approved`` subscribed and approved
    - ``unsubscribed`` explicitly excluded from the group
    - ``expired`` subscription validity (gueltig_von, gueltig_bis) expired

.. note::
    When evaluating if a person or email is subscribed, check for either
    ``subscribed`` or ``approved``, as both denote an active subscription.


``steuerung_bit``
"""""""""""""""""""""""""""""
Specifies whether the subscription is positive (e.g. I want this newsletter)
or negative, (Never send this again). The default is ``True``.

.. attention::
    Setting this to ``False`` denotes and **explicit exclusion**
    from the group.

.. _gueltig_von:

``gueltig_von``, ``gueltig_bis``
""""""""""""""""""""""""""""""""
Specifies the validity for the subscription. The default for new entries
is from ``today`` to ``2099-12-31`` (forever).

When the ``state`` is ``subscribed`` or ``approved``, the two fields can be
altered to automatically start or expire a subscription depending on the current
date.

.. note::
    If the associated :ref:`frst_zgruppedetail` has ``bestaetigung_erforderlich``
    set to ``True``, these dates will temporarily be set to ``1999-09-09``
    until the subscription was approved. After approvement, the default
    values are used.


``bestaetigt_am_um``
"""""""""""""""""""""""""""""
The date and time when the subscription was approved. ``Null`` if it the
subscription was not approved yet.

``bestaetigt_typ``
"""""""""""""""""""""""""""""
Specifies how this subscription was approved. Possible values are:
 - ``doubleoptin`` subscription was approved via double opt in
 - ``phone_call`` a staffer approved the subscription in a phone call
 - ``workflow`` a Fundraising Studio workflow handled the affirmation

``bestaetigt_herkunft``
"""""""""""""""""""""""""""""
May contain a reference for the affirmation process. For eample, this
could be a web link or a workflow identifier.

.. _common_required_fields:

Common required fields
----------------------

``zgruppedetail_id``
"""""""""""""""""""""""""""""
Foreign key to the :ref:`frst_zgruppedetail`.

.. note::
    You can only assign a :ref:`frst_zgruppedetail`, whose
    :ref:`frst_zgruppe` has a ``tabellentyp_id`` matching the
    subscription.

    That means, when - for example - creating an email subscription,
    you can only assign groups intended for emails. Assigning an
    occupation group would fail.

.. _frst_persongruppe:

frst.persongruppe
-----------------
Represents a subscription for a person. For example: occupation.

.. attention::
    Depending on the associated :ref:`frst_zgruppedetail`, the supplied
    validity dates might be discarded due to the affirmation process.

    See :ref:`gueltig_von` for details.

Required fields
"""""""""""""""
(In addition to the :ref:`common_required_fields`)

``partner_id``
"""""""""""""""""""""""""""""
Foreign key to the :ref:`res_partner`.

.. _frst_personemailgruppe:

frst.personemailgruppe
----------------------
Represents a subscription for an email. For example: newsletter.

.. attention::
    Depending on the associated :ref:`frst_zgruppedetail`, the supplied
    validity dates might be discarded due to the affirmation process.

    See :ref:`gueltig_von` for details.

Required fields
"""""""""""""""
(In addition to the :ref:`common_required_fields`)

``frst_personemail_id``
"""""""""""""""""""""""""""""
Foreign key to the :ref:`frst_personemail`.
