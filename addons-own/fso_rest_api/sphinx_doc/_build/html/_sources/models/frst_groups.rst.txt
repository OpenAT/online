.. _frst_groups:

================================
frst.zgruppe, frst.zgruppedetail
================================

These records represent Fundraising Studio group folders. It works similar
to a tagging system, but has a start and end date associated, and a 1-deep
hierarchy: :ref:`frst_zgruppe` can
be viewed as a container for multiple :ref:`frst_zgruppedetail`.

.. _frst_zgruppe:

frst.zgruppe
------------
Parent for :ref:`frst_zgruppedetail`.

Defines the meaning of groups contained and specifies if the groups within
can be assigned to people, or emails, or contracts, etc..

Example:
 - :ref:`frst_zgruppe` "Beruf" (occupation)
    - :ref:`frst_zgruppedetail` "Angestellte/r" (employee)
    - :ref:`frst_zgruppedetail` "Arbeiter/in" (laborer)
    - :ref:`frst_zgruppedetail` "Pensionist/in" (retiree).

.. note::
    Only reading is supported for this model.

Special Fields
""""""""""""""""""""""

``gruppe_lang``
""""""""""""""""""""""
The name or title of the group.


``tabellentyp_id``
""""""""""""""""""""""
Specifies the target type for the contained groups. It can be one of the
following values:

    - ``100100`` group is for people, e.g.: occupation
    - ``100110`` groups is for email addresses, e.g.: newsetter

.. note::
    There several more types, but only the the listed values are
    currently supported by the API.

``gui_anzeigen``
""""""""""""""""""""""
Specifies whether the group is active for this organisation.

.. note::
    When :ref:`searching`, only use entries having the value ``True``.

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.

.. _frst_zgruppedetail:

frst.zgruppedetail
----------------------
Child of :ref:`frst_zgruppe`.

Represents an actual value within a group. It could be a
specific occupation, or a specific newsletter group.

Example:
 - :ref:`frst_zgruppe` "Beruf" (occupation)
    - :ref:`frst_zgruppedetail` "Angestellte/r" (employee)
    - :ref:`frst_zgruppedetail` "Arbeiter/in" (laborer)
    - :ref:`frst_zgruppedetail` "Pensionist/in" (retiree).

Required Fields
"""""""""""""""
The minimum requirements for a new group entry are:
    - ``zgruppe_id``
    - ``geltungsbereich``
    - ``gruppe_lang``
    - ``gui_anzeigen``

.. note::
    ``geltungsbereich`` can only be ``local`` for new groups.
    ``gui_anzeigen`` must be ``True``, otherwise the entry is
    considered to be not in use.

.. note::
    If not specified, the default values are:
     - ``today`` for ``gueltig_von`` and
     - ``2099-12-31`` (forever) for ``gueltig_bis``

Special Fields
""""""""""""""""""""""

``zgruppe_id``
"""""""""""""""""""""
The foreign key to the parent :ref:`frst_zgruppe` record.

``geltungsbereich``
"""""""""""""""""""""
Differentiates between ``system`` groups, and ``local`` groups.
Custom records must be ``local``, anything else is invalid.

``bestaetigung_erforderlich``
"""""""""""""""""""""""""""""

If ``True``, the group requires confirmation before being considered
active.

.. attention::
    Setting this to ``True`` affect s the behaviour for new subscriptions.
    See :ref:`frst_group_subscriptions` for details.

``bestaetigung_typ``
"""""""""""""""""""""
Specifies the type of confirmation. It can be one of the following values:
 - ``doubleoptin`` group only activates upon confirmation
 - ``phone_call`` a staffer confirmed the group in a phone call
 - ``workflow`` confirmation is handled via Fundraising Studio workflow


Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
