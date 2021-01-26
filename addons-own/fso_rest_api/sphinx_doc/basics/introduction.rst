==================================
Introduction
==================================

The Fundraising Studio Rest API provides an interface to some of the most common models and methods of
Fundraising Studio. We provide an openapi 2.0 (former known as swagger) specification file in json format to make
it easy for any developer to use the api with simple http requests. We also provide a "swagger ui" client
where you can view the content of the specification file and execute http request directly.

Available Operations (Methods):

* create
* read
* write (update)
* delete
* search via **call-method**
* additional methods via **call-method**

Available Models:

* Contacts (Persons)
* E-Mail Addresses of Persons (PersonEmail)
* Group Folders
* Groups
* Group Assignments (Subscriptions)
* Products
* Donations and Sale Orders
* Payment Transactions

Where to start?
---------------

If you are familiar with `openapi <https://www.openapis.org/>`__ (`swagger <https://swagger.io/specification/v2/>`__)
and REST API's in common we recommend to jump right into the :ref:`basic_tutorial`. Here you will find an example of how
to authenticate at the system, send basic commands and interpreting the returning data as well as information about
exceptions and gotchas. After the basic tutorial you may get your self an overview of the models and methods available
to you.


