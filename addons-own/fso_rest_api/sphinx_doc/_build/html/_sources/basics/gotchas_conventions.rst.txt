.. _gotchas_and_conventions:

==================================
Gotchas and Conventions
==================================

Please read this part of the documentation very carefully because it may save you und us a lot of troubles
and working hours.

Charset
-------

The charset is always **UTF-8** no matter what you set in the header like e.g. in **charset** ``'charset': 'utf-8'``
or in **Content-Type** ``'Content-Type': 'application/json; charset=utf-8'``.

Content-Type
------------
The content type is always ``application/json`` no matter what you set in the header or elsewhere. If you try
to set an other content type you will get an error in return.

Calling model methods
---------------------
Some methods require no parameters. In those cases, be sure to provide an empty
dictionary in the request.

.. tabs::

    .. code-tab:: python
        :emphasize-lines: 4

            # This is fine
            response = requests.patch(api_base_url + '/frst.personemailgruppe/call/deactivate/43,88,120',
                                    headers={'accept': 'application/json'},
                                    json={},
                                    auth=auth)

            # This will fail
            response = requests.patch(api_base_url + '/frst.personemailgruppe/call/deactivate/43,88,120',
                                    headers={'accept': 'application/json'},
                                    auth=auth)

If you do not send an empty dictionary, you will get an error like this:

.. error::
    Function declared as capable of handling request of type 'apijson' but called with a request of type 'http'

Date and Datetime Fields
------------------------

All date and datetime fields are of type "string" and not of type date or datetime. This is due to historical reasons.
Such fields are marked in the json specification with *$date* or **$datetime** like ``string($date)``. You have to use
the following format for all fields marked with $date or $datetime:

    | DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
    | DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
    | DEFAULT_SERVER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    | Example: ``2021-02-08 15:16:59``

.. attention:: All dates and datetimes are read and written as **UTC**! Please provide and interpret any datetime data
    accordingly!

Locale
------

Locale settings will be taken from the default language ``de_DE``.

Language
--------

The API supports only german (``de_DE``). Therefore all fields that are translateable will be read and
written as german.


