.. _access_security:

==================================
Access and Security
==================================

The API grants access to the ``create``, ``read``, ``write``, ``delete`` and the :ref:`search <searching>` methods
of the models described in this documentation.

This global access can be further restricted by the user rights of the user linked to the ``api-user-token``.

.. attention:: In most models you may only be able to delete records that where created by your user
    (user of your ``api-user-token``)! Deletion of records created by other users will fail with an access error.

    In some cases you may not be able to delete records even if they where created by your api user. This is most
    likely due to some linked documents that must be deleted manually before the deletion of the record.

User with restricted rights
---------------------------

We **strongly** advise you to request a unique user (``api-user-token``) for different applications and usages
scenarios with tailored user rights. This enhances the security and will prevent errors on the client side.

We can even provide you with a custom API to enhance the security even further if only a very small
subset of models or methods are needed in your application.


Security advisory
-----------------

It is in your responsibility to protect the provided ``api-user-tokens``. Never send them over any
unprotected protocols or expose them unprotected. Tokens may be revoked by us at any time if suspicious
traffic or usage is detected.

As a rule of thumb tokens should be renewed at least every six months.





