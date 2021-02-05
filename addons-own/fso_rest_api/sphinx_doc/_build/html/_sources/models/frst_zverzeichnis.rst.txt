.. _frst_zverzeichnis:

=========================================
frst.zverzeichnis
=========================================

Records of this model represent the campaign directory system,
also known as CDS. It consists of directories and lists within
a hierarchy.

.. note::
    The CDS does not have a fixed structure from one organisation to
    the next. It is advised to consult with the organisation on whether
    new entries should be created, or existing ones should be
    referenced.

.. attention::
    The CDS impacts many areas, like accounting, statistics, workflows,
    selections and more.
    Great care must be taken, especially when altering existing records.

Required Fields
---------------
The minimum requirements for a new CDS entry, are:
    - ``verzeichnisname``

This will create a top level CDS folder by default.

Special Fields
--------------

``verzeichnistyp_id``
"""""""""""""""""""""
Defines, whether this CDS entry is a directory, or a list.
 - ``True`` to denote directories
 - ``False`` to denote lists


``bezeichnungstyp_id``
""""""""""""""""""""""
Defines the type for the entry, which can be one of the following
key words:
 - ``KA`` for campaigns
 - ``Aktion`` for actions
 - ``ZG`` for a target audiences

``parent_id``
""""""""""""""""""""""
The foreign key for the parent element.

.. attention::
    When creating a hierarchy, make sure that the ``parent_id`` is
    either ``null``, or another directory.
    Lists must not be the parent of other CDS entries.

``startdatum``
""""""""""""""
The start date of the campaign. It defaults to the current day.

``endedatum``
"""""""""""""
The end date of the campaign. It defaults to ``2099-12-31``, which
is treated as having no end.

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.
