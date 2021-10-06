.. _models_overview:

===========================================
Models Overview
===========================================

The models below are the most common models accessed through the Fundraising Studio API.
The full list of available models with their fields and data types can be found in the openapi specification file.

.. contents:: Common Models
    :depth: 1
    :local:

--------------------------------------------------------------------------------------------------------------------

Country
--------------------------------------------------------------

:ref:`res_country`

Countries known by the system.


Currency
--------------------------------------------------------------

:ref:`res_currency`

Currencies known by the system.


Payment intervals
--------------------------------------------------------------

:ref:`product_payment_interval`

Recurring payment intervals known by the system.


Payment interval lines
--------------------------------------------------------------

:ref:`product_payment_interval_lines`

Assigns possible payment intervals to a :ref:`product_template`.


Partner
--------------------------------------------------------------

:ref:`res_partner`

A :ref:`res_partner` record represents most likely a person.
This may be a donor, an employee or any other kind of contact.

.. hint::

    A res.partner record may also be called: **Person**, **Spender**, **Donor**, **Partner** or **Contact** throughout
    this documentation!

A partner may have multiple email addresses :ref:`frst_personemail` and may be assigned to many partner groups
:ref:`frst_persongruppe`.

Email Addresses
---------------------------------------

:ref:`frst_personemail`

A :ref:`frst_personemail` record represents an email address of a partner.
Two partners may have identical email addresses but the emails must be unique per partner.

The ``email`` of the *main email address* :ref:`frst_personemail` record will show up in the :ref:`res_partner`
field ``email`` also. Check the :ref:`frst_personemail` documentation for more information about
*main email address* handling!

Groups
-------------------------

:ref:`frst_groups`

Fundraising Studio Groups are very versatile and therefore used for many, many things.
They can be assigned to :ref:`partner <res_partner>`, :ref:`email addresses <frst_personemail>` and a lot of other
models.

The most important use case may be the subscription of email addresses to mailing lists as well as the assignment
of groups to a partner to opt-out or opt-in for communication channels (email, sms) as well as for accounting
relevant settings like the *donation report submission* to the austrian tax office.

Group Subscriptions
---------------------------------------------------

:ref:`frst_group_subscriptions`

An assignment of a group to a record is called *group subscription* or just subscription. These assignments
or *group subscription records* have a status that indicates if this assignment is e.g. *active*, *expired* or
*waiting for approval*.

The most important use case may be to handle subscription to mailing lists or in other words to handle
:ref:`subscriptions <frst_personemailgruppe>` of :ref:`email addresses <frst_personemail>` to
:ref:`mailing groups <frst_zgruppedetail>` (e.g. subscriptions to the newsletter group).

The full relation for email subscriptions would be:

:ref:`res_partner` < :ref:`frst_personemail` < :ref:`frst_personemailgruppe` > :ref:`frst_zgruppedetail` > :ref:`frst_zgruppe`

Relation for groups assigned to a partner:

:ref:`res_partner` < :ref:`frst_persongruppe` > :ref:`frst_zgruppedetail` > :ref:`frst_zgruppe`

Fundraising Studio CDS
-----------------------------------------------

:ref:`frst_zverzeichnis`

The Fundraising Studio CDS (or *Verzeichnis*) is a tree like structure to link any kind of document to it like
Contracts, Donations, Leads and many more. It can be imagined like a traditional folder structure where you can
put your documents into. The linkage of documents to the CDS may have an impact (among other things) on reports
and how accounting entries are handled.

.. hint::

    **CDS folders may also represent campaigns:**

    You are able to link actions (mail, email, sms, contracts) to a cds record for cumulative reporting and
    centralized monitoring.


Products
--------------------------------------------------------------

:ref:`products`

``product.template`` represents both donation products or physical products. ``product.product`` represents
a variant of that product.

By default, products (especially donation products), have only one variant, which is automatically created, when
creating the ``product.template``.

.. warning:: Multiple variants are currently not supported.

Sale orders & Donations
--------------------------------------------------------------

:ref:`sale_orders`

``sale.order`` represents an order, and ``sale.order.line`` represents an order line.

An order can contain multiple lines.

Payment acquirer
--------------------------------------------------------------

:ref:`payment_acquirer`

Specifies how a payment was acquired.


Payment transaction
--------------------------------------------------------------

:ref:`payment_transaction`

Represents an actual payment, including all the payment specific information.


Mail Message (Comments)
--------------------------------------------------------------

:ref:`mail_message`

Represents a message or comment.

Mail Message Subtype
--------------------------------------------------------------

:ref:`mail_message_subtype`

Categorizes messages and comments.
