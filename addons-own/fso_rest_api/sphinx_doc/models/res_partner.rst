.. _res_partner:

==================
res.partner
==================

Records of this model represent a person or a company. This may be a donor, an employee or any other kind
of contact.

.. note::

    Some of the records in this model may stand for special forms of partner data such as
        - rental addresses
        - invoice partner/address
        - delivery partner/address
        - deleted partners (where some data must be kept for accounting reasons)

.. attention::

    Currently the API is not supporting multiple (postal) addresses per partner. But you can set and manipulate the
    *current address* or *main address* by setting the corresponding fields of the :ref:`res_partner` record like
    ``street``, ``country_id``, ``zip`` and so on! Managing multiple addresses per partner  is therefore only
    available through the Fundraising Studio GUI but may be added later to the REST API.

.. attention::

    Currently the API is not able to set or read the relations between partner! This feature is therefore only
    available through the Fundraising Studio GUI but may be added later to the REST API.

Required Fields
---------------
The minimum requirement for a new contact are the fields ``lastname`` and ``email``.

Fields
---------------

``id``
""""""""""""""""""""""""""""""
The identity column for the partner.

``firstname``
""""""""""""""""""""""""""""""
The first name of the partner.

``lastname``
""""""""""""""""""""""""""""""
The last name of the partner.

``name_zwei``
""""""""""""""""""""""""""""""
Additional name field.

``company_name_web``
""""""""""""""""""""""""""""""
Name for organisations or companies.

``birthdate_web``
""""""""""""""""""""""""""""""
Birthdate for the partner.

``frst_zverzeichnis_id``
""""""""""""""""""""""""""""""
The :ref:`frst_zverzeichnis` for the origin of the partner. Get this ID from the organisation or from DataDialog or
create one via the API.

``gender``
""""""""""""""""""""""""""""""
Gender of the partner, can be either

- ``male``
- ``female``
- ``other``

``title_web``
""""""""""""""""""""""""""""""
Title of the partner.

``phone``
""""""""""""""""""""""""""""""
The land line phone number.


``mobile``
""""""""""""""""""""""""""""""
The mobile phone number.

``fax``
""""""""""""""""""""""""""""""
The fax number.

``street``
""""""""""""""""""""""""""""""
The street of the postal address.

``street_number_web``
""""""""""""""""""""""""""""""
The street number of the postal address.

``city``
""""""""""""""""""""""""""""""
The city of the postal address.

``zip``
""""""""""""""""""""""""""""""
The ZIP number or postal code of the postal address.

``country_id``
""""""""""""""""""""""""""""""
The :ref:`res_country` foreign key for the nationality of the partner.

``email``
""""""""""""""""""""""""""""""
The main E-Mail address of the partner. This is automatically synchronized with the
:ref:`frst_personemail` model, which holds all E-Mail addresses for a partner.

``main_personemail_id``
""""""""""""""""""""""""""""""
Foreign key to the main :ref:`frst_personemail`.

``frst_personemail_ids``
""""""""""""""""""""""""""""""
Foreign key list of all the :ref:`frst_personemail` of the partner.

``newsletter_web``
""""""""""""""""""""""""""""""
If true, subscribe the partners main E-Mail address to the default newsletter of the organisation.

``gdpr_accepted``
""""""""""""""""""""""""""""""
If true, the partner accepted the GDPR notice.

``donation_deduction_optout_web``
"""""""""""""""""""""""""""""""""
The partner does not want to deduct his donation from taxes.

``bpk_forced_firstname``
"""""""""""""""""""""""""""""""""
When querying the Austrian BPK number, use this first name instead of the partners first name.
Leave empty unless required for tax deduction. If using ``bpk_forced``, all ``bpk_forced_*`` fields
are required.

``bpk_forced_lastname``
"""""""""""""""""""""""""""""""""
When querying the Austrian BPK number, use this last name instead of the partners last name.
Leave empty unless required for tax deduction. If using ``bpk_forced``, all ``bpk_forced_*`` fields
except ``zip`` and ``street`` are required.

``bpk_forced_birthdate``
"""""""""""""""""""""""""""""""""
When querying the Austrian BPK number, use this birthdate instead of the partners birth date.
Leave empty unless required for tax deduction. If using ``bpk_forced``, all ``bpk_forced_*`` fields
except ``zip`` and ``street`` are required.


``bpk_forced_zip``
"""""""""""""""""""""""""""""""""
When querying the Austrian BPK number, use this ZIP/postal code instead of the partners ZIP/postal code.
Leave empty unless required for tax deduction. If using ``bpk_forced``, all ``bpk_forced_*`` fields
except ``zip`` and ``street`` are required.


``bpk_forced_street``
"""""""""""""""""""""""""""""""""
When querying the Austrian BPK number, use this street instead of the partners street.
Leave empty unless required for tax deduction. If using ``bpk_forced``, all ``bpk_forced_*`` fields
except ``zip`` and ``street`` are required.

Special Fields
--------------

``name``
""""""""""

The ``name`` field of a partner is a computed field based on the fields ``firstname`` and ``lastname``.
Therefore ``name`` should NEVER be used if ``firstname`` and ``lastname`` are known.

If only ``name`` is given at partner creation the string will be split at the first ``space`` and the first part of the
string will be in ``firstname`` and the rest of the string in ``lastname``. If there is no space in the string the
full string will go into ``lastname``.

.. tip:: ``name`` can be very handy in :ref:`searching` for partners!

.. _res_partner_nob_email:

``email``
""""""""""

A partner in Fundraising Studio can have multiple email addresses stored in :ref:`frst_personemail` and linked to the
partner by the field ``frst_personemail_ids``. These e-mail addresses are created and linked indirectly
by the char field ``email`` of the partner.

If a new email is entered in the field ``email`` of the partner a new :ref:`frst_personemail` will be
created and linked automatically to the partner. The last email entered will be the so called *current* or
*main email address*.

The *main email address* will always match the email found in the :ref:`res_partner` field ``email`` and is linked
for convenience only in the :ref:`res_partner` field ``main_personemail_id``

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
