.. _introduction:

==================================
Introduction
==================================

The :ref:`Fundraising Studio Rest API <fundraising_studio_rest_api>` provides an interface to some of the most common
models and methods of `Fundraising Studio <https://www.datadialog.net>`__. We provide an openapi 2.0
(former known as swagger) specification file in json format to make it easy for any developer to use the
api with simple http requests. We also provide a "swagger ui" client where you can view the content of
the specification file and execute http request directly.

Areas of application:

    * Management of Partner (Contacts, Persons)
    * Management of E-Mail Addresses
    * Management of Groups and Group Subscriptions
    * Management of Mailing Lists and Subscriptions
    * Double-Opt-In Settings for Mailing List Subscriptions

Areas of application in the near future:

    * Import of (online) donations
    * Import and update of (online) payments
    * Management of FS-Online Donation Forms
    * Management of FS-Online E-Mail Templates
    * Management of FS-Online Surveys
    * Management of FS-Online Forms
    * Management of the FS-Online E-Commerce Webshop

Where to start?
---------------

If you are familiar with `openapi <https://www.openapis.org/>`__ (`swagger <https://swagger.io/specification/v2/>`__)
and REST API's in common we recommend to jump right into the :ref:`basic_tutorial`. Here you will find an example of how
to authenticate at the system, send basic commands and interpreting the returning data as well as information about
exceptions and gotchas. After the basic tutorial you may get your self an
:ref:`overview of the models and methods <models_overview>` and finally jump to the :ref:`use_cases` for some real
world examples.
