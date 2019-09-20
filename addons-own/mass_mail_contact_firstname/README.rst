.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

================================
Partner first name and last name
================================

This module was written to extend the functionality of contacts to support
having separate last name and first name.

Configuration
=============

You can configure some common name patterns for the inverse function
in Settings > Configuration > General settings:

* Lastname Firstname: For example 'Anderson Robert'
* Lastname, Firstname: For example 'Anderson, Robert'
* Firstname Lastname: For example 'Robert Anderson'

After applying the changes, you can recalculate all partners name clicking
"Recalculate names" button. Note: This process could take so much time depending
how many partners there are in database.

You can use *_get_inverse_name* method to get lastname and firstname from a simple string
and also *_get_computed_name* to get a name form the lastname and firstname.
These methods can be overridden to change the format specified above.


Usage
=====

The field *name* becomes a stored function field concatenating the *last name*
and the *first name*. This avoids breaking compatibility with other modules.

Users should fulfill manually the separate fields for *last name* and *first
name*, but in case you edit just the *name* field in some unexpected module,
there is an inverse function that tries to split that automatically. It assumes
that you write the *name* in format configured (*"Lastname Firstname"*, by default),
but it could lead to wrong splitting (because it's just blindly trying to
guess what you meant), so you better specify it manually.

For the same reason, after installing, previous names for contacts will stay in
the *name* field, and the first time you edit any of them you will be asked to
supply the *last name* and *first name* (just once per contact).


Known issues / Roadmap
======================

Patterns for the inverse function are configurable only at system level. Maybe
this configuration could depend on partner language, country or company,
as discussed at `this OCA issue <https://github.com/OCA/partner-contact/issues/210>`_


Credits
=======

Contributors
------------

* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Jonathan Nemry <jonathan.nemry@acsone.eu>
* Olivier Laurent <olivier.laurent@acsone.eu>
* Hans Henrik Gabelgaard <hhg@gabelgaard.org>
* Jairo Llopis <j.llopis@grupoesoc.es>
* Adrien Peiffer <adrien.peiffer@acsone.eu>
* Antonio Espinosa <antonioea@antiun.com>

