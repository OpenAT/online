# -*- coding: utf-8 -*-

"""
facebook question types
-------------------------
FULL_NAME - full person name
FIRST_NAME
LAST_NAME
GENDER
RELATIONSHIP_STATUS

COMPANY_NAME

DOB - date of birth

STREET_ADDRESS
CITY
STATE
COUNTRY
POST_CODE

JOB_TITLE

EMAIL - email addresses
WORK_EMAIL
PHONE - phone numbers
WORK_PHONE_NUMBER

CUSTOM - custom text, drop downs
DATE_TIME - date and time
STORE_LOOKUP - lookup fields (e.g. locations via location manager)

ID_... - Government-issued ID (various types, e.g. ID_AR_DNO,
         see https://developers.facebook.com/docs/marketing-api/guides/lead-ads/create)

"""

facebook_field_type_to_odoo_field_name = {
    'FULL_NAME': 'partner_name',
    'FIRSTNAME': 'firstname',
    'LASTNAME': 'lastname',
    'EMAIL': 'email_from',
    'PHONE': 'phone',
    'STREET_ADDRESS': 'street',
    'CITY': 'city',
    'POST_CODE': 'zip',
}

facebook_graph_api_url = "https://graph.facebook.com/v6.0/"
