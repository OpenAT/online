.. _mail_message:

=========================================
mail.message
=========================================

Contains messages or comments. The comment can be assigned to either a person or a
sale order via the ``model`` field.

Example:
    A donor donates for the product "Fight animal cruelty". The form contains a comment field.
    In the comment field, the donor writes "Use my donation for dogs only." - this text would
    be sent via ``mail.message``, with the target model ``sale.order``.

.. note:: Only creating is supported for this model.

Fields
------
- ``subject`` An optional subject line
- ``body`` The actual message or comment
- ``model`` The model the comment is referencing, currently only the following are supported:

    - ``res.partner``
    - ``sale.order``

- ``res_id`` The foreign key to the model specified in the field ``model``
- ``type`` Can be either

    - ``email``
    - ``comment`` Use this.
    - ``notification``

- ``subtype_id`` Foreign key to the subtype of the message or comment. See :ref:`mail_message_subtype`

Methods
-------

``search``
""""""""""

Only the ``search`` method is currently exposed by the api. See :ref:`searching` for more information about searching.


.. _mail_message_subtype:

=========================================
mail.message.subtype
=========================================

Further categorizes the email, comment or notification.

Generally, look up the ``id`` for one of these subtypes when sending comments:

- ``FS-Online Change Bank Account Request`` for comments that request changes for the bank account
- ``FS-Online Change Contract Request`` for comments that request changes for the (recurring) contract
- ``FS-Online Question / Survey`` for general comments

