.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Website Global PopUp-Promo-Box
==============================

This module allows you to display a PopUpBox modal dialog on every wegpage. The user
is able to hide the PopUpBox throug a button for his entire session.
The PopupBox can be used to promote important content or collect newsletter subscriptions
and alike.

Usage
=====

Simply set some content for the PopUpBox and a start date:

1. Go to ``/website_popup/edit`` to edit the content inside the PopUpBox as well as the button text
2. Set the start-date and optionally an end-date in the website settings
3. Re-enable the PopUpBox  by visiting ``/website_popup/enable`` to check the display

HINT: The PopUpBox will not show up without a start date. The end date is optional.

HINT: Step two will disable the display of the PopUpBox for the current session so don't
forget step three if you want to check the final look of the PopUpBox.

URLS
====

You can use these configuration URLs to set the PopUpBox Content or to
disable or enable the PopUpBox for your current Session

- ``/website_popup/edit``
- ``/website_popup/cancel``
- ``/website_popup/enable``

Example: http://your.site.com/website_popup/edit

Tips and Tricks
===============

Some neat little Extras you may find useful:

Re-Enable PopUpBox after some time
----------------------------------

If you want the PopUpBox to be displayed again after some time you could combine it with an
addon like web_sessions_management from yelizariev to clear user sessions after a some time.

Create links that will not show the PopUpBox at first
-----------------------------------------------------

If you want to create a link to one of your pages but do not want to show the PopUpBox straight away
you could add ``no_popup_box=True`` to your url arguments. This will prevent the box to show up
until the users visits some other page of the website. e.g.:
``http://your.site.com/?no_popup_box=True``

Position the box at the bottom
------------------------------

You can use this css to position the box at the bottom:

``
#popupbox.modal {
    top: auto;
}
``

**WARNING:** this will disable the vertical scrolling so make sure to disable this again for
smaller widths and small devices through media queries.

Credits
=======

This addon was created by Datadialog. For more information please visit http://www.datadialog.net

Contributors
------------

* Michael Karrer <michael.karrer@datadialog.net>

