# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# ----------------
# This implements:
#     - THE BINDING ODOO MODEL (delegated inheritance)
#       Holds the external id and internal id as well as additional fields/info not needed in the inherited models
#     - THE BINDER
#       Methods to get the odoo record based on the getresponse id and vice versa
#     - THE ADAPTER
#       Send or get data from the getresponse api, implements the CRUD methods and searching
# ----------------

# !!!!!!!!!
# PITFALLS:
# !!!!!!!!!
# - The getresponse-python lib will return objects! Sometimes GetResponse will not return all fields of an object!
#   Therefore it may appear that a field is 'unset' or False just because it was not returned by GetResponse!
#   There are two ways to check if a field was not returned or was returned but empty:
#     1. If the field value is False it was returned but empty - if it is Null it was not returned
#     2. Check if the field is in raw_data['kwargs'] ! This is the raw response data from GetResponse!
# - If you update a contact (POST to /contact/id) 'tags' and 'customFieldValues' will REPLACE all the existing TAGS
#   and/or custom fields !!! So make sure the contact data in FS-Online is 'up-to-date' with GetResponse before
#   exporting tags or custom fields!

import logging
from getresponse.excs import NotFoundError

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.exception import IDMissingInBackend

from .backend import getresponse
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder

_logger = logging.getLogger(__name__)


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseContact(models.Model):
    _name = 'getresponse.frst.personemailgruppe'
    _inherits = {'frst.personemailgruppe': 'odoo_id'}
    _description = 'GetResponse Contact (Subscription) Binding'

    _sync_allowed_states = ['subscribed', 'approved']

    backend_id = fields.Many2one(
        comodel_name='getresponse.backend',
        index=True,
        string='GetResponse Connector Backend',
        required=True,
        readonly=True,
        ondelete='restrict'
    )
    odoo_id = fields.Many2one(
        comodel_name='frst.personemailgruppe',
        inverse_name='getresponse_bind_ids',
        index=True,
        string='Fundraising Studio Subscription',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    getresponse_id = fields.Char(
        string='GetResponse Contact ID',
        readonly=True
    )
    sync_date = fields.Datetime(
        string='Last synchronization date',
        readonly=True)

    # ATTENTION: This will be filled/set by the generic binder bind() method in unit_binder.py!
    #            We use this data to check for concurrent writes
    sync_data = fields.Char(
        string='Last synchronization data',
        readonly=True)

    # ATTENTION: !!! THE 'getresponse_uniq' CONSTRAIN MUST EXISTS FOR EVERY BINDING MODEL !!!
    # TODO: Check if the backend_uniq constrain makes any problems for the parallel processing of jobs
    _sql_constraints = [
        ('getresponse_uniq', 'unique(backend_id, getresponse_id)',
         'A binding already exists with the same GetResponse ID for this GetResponse backend (Account).'),
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A binding already exists for this odoo record and this GetResponse backend (Account).'),
    ]


class GetResponseFrstZgruppedetail(models.Model):
    _inherit = 'frst.personemailgruppe'

    getresponse_bind_ids = fields.One2many(
        comodel_name='getresponse.frst.personemailgruppe',
        inverse_name='odoo_id',
    )


# ----------------
# CONNECTOR BINDER
# ----------------
@getresponse
class ContactBinder(GetResponseBinder):
    _model_name = ['getresponse.frst.personemailgruppe']

    _sync_allowed_states = ['subscribed', 'approved']
    _bindings_domain = [('zgruppedetail_id.sync_with_getresponse', '=', True),
                        ('state', 'in', _sync_allowed_states)
                        ]

    # Make sure only personemailgruppe with sync enabled campaign and allowed state will get a prepared binding
    # HINT: get_unbound() is used by prepare_bindings() which is used in the batch exporter > prepare_binding_records()
    #       and in helper_consumer.py > prepare_binding_on_record_create() to filter out records where no binding
    #       should be prepared (created) for export.
    def get_unbound(self, domain=None):
        domain = domain if domain else []
        domain += self._bindings_domain
        unbound = super(ContactBinder, self).get_unbound(domain=domain)
        return unbound

    # Make sure only bindings with sync enabled campaign and allowed state are returned
    # HINT: get_bindings() is used in single record exporter run() > _get_binding_record() to filter and validate
    #       the binding record
    def get_bindings(self, domain=None):
        domain = domain if domain else []
        domain += self._bindings_domain
        bindings = super(ContactBinder, self).get_bindings(domain=domain)
        return bindings


# -----------------
# CONNECTOR ADAPTER
# -----------------
# The Adapter is a subclass of an ConnectorUnit class. The ConnectorUnit Object holds information about the
# connector_env, the backend, the backend_record and about the connector session
@getresponse
class ContactAdapter(GetResponseCRUDAdapter):
    """
    ATTENTION: read() and search_read() will return a dict and not the getresponse_record itself but
               create() and write() will return a getresponse object from the getresponse-python lib!
    """
    _model_name = 'getresponse.frst.personemailgruppe'
    _getresponse_model = 'contact'

    # ATTENTION: !!! A segments search will NOT return all the fields! E.g. custom fields or tags will be missing!
    def search(self, getresponse_campaign_ids=None, name=None, email=None, custom_fields=None, **kwargs):
        """ Returns a list of GetResponse contact ids

        'name', 'email' and 'custom_fields' are optional easy search attributes

        available operators: 'is', 'is_not', 'contains', 'not_contains', 'starts', 'ends', 'not_starts', 'not_ends'

        :param getresponse_campaign_ids: list
        :param name: list of strings
            tuple format: (operator, value)
        :param email: tuple or string
            tuple format: (operator, value)
        :param custom_fields: list
            format: [(getresponse_custom_field_id, operator, value)]

        :return: list
            returns a list with the getresponse contact ids (external ids)
        """
        # HINT: get_all_contacts will do 4 searches to find contacts for all subscriber types - therefore it will
        #       return ALL contacts! (=including non approved or inactive contacts)
        # ATTENTION: !!! A segments search will NOT return all the fields! E.g. custom fields or tags will be missing!
        #            This is not a real problem here because we return only the list of id's anyway!
        contacts = self.getresponse_api_session.get_all_contacts(campaign_ids=getresponse_campaign_ids,
                                                                 name=name,
                                                                 email=email,
                                                                 custom_fields=custom_fields,
                                                                 **kwargs)
        return [contact.id for contact in contacts]

    def read(self, ext_id, attributes=None):
        """ Returns the information of one record found by the external record id as a dict """
        contact = self.getresponse_api_session.get_contact(ext_id, params=attributes)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return contact.__dict__

    def search_read(self, filters=None):
        """ Search records based on 'filters' and return their information as a dict
        Retrieve approved contacts from all campaigns.
        ATTENTION: This will NOT return non approved contacts!

        Args:
            filters:
                query: Used to search only resources that meets criteria.
                You can specify multiple parameters, then it uses AND logic.

                fields: List of fields that should be returned. Id is always returned.
                Fields should be separated by comma

                sort: Enable sorting using specified field (set as a key) and order (set as a value).
                You can specify multiple fields to sort by.

                page: Specify which page of results return.

                perPage: Specify how many results per page should be returned

                additionalFlags: Additional flags parameter with value 'exactMatch' will search contacts
                with exact value of email and name provided in query string. Without that flag matching
                is done via standard 'like' comparison, what could be sometimes slow.

        Examples:
            search_read({"query[name]": "XYZ"})
        """
        contacts = self.getresponse_api_session.get_contacts(filters)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return contacts.__dict__

    # TODO: Handle 'contact exists' or 'non unique value' exceptions
    def create(self, data):
        """ Create a Contact

        Returns:
            bool: True for success, False otherwise
        """
        # ATTENTION: The contact may not be created immediately by GetResponse - Therefore we will only get a
        #            boolean result. Therefore we can not bind the contact immediately!!!
        boolean_result = self.getresponse_api_session.create_contact(data)
        assert boolean_result, "Could not create contact in GetResponse!"
        return boolean_result

    # TODO: Handle NotFoundError exceptions
    # ATTENTION: PLEASE CHECK 'PITFALLS' COMMENT AT THE START OF THE FILE!
    def write(self, ext_id, data):

        # UPSERT CUSTOM FIELDS
        # TODO: This will be replaced by a more sophisticated thing because upsert can never 'clear' (set empty)
        #       a custom field!!!
        # Only append/update custom field values in GetResponse but do not replace 'customFieldValues'!
        custom_field_values = data.pop('customFieldValues', None)
        if custom_field_values:

            # TODO: remove all custom fields with empty values because you can not unset/delete on upsert
            for index, cf in enumerate(custom_field_values):
                # HINT: x2Many fields are not supported yet - therefore the first value is the only one ;)
                if not cf['value'][0]:
                    custom_field_values.pop(index)

            cfv_payload = {'customFieldValues': custom_field_values}
            cfv_upsert_result = self.getresponse_api_session.upsert_contact_custom_fields(ext_id, cfv_payload)
            assert len(custom_field_values) == len(cfv_upsert_result.get('customFieldValues', [])), (
                "Upsert (add or update) of custom fields failed!")

        # UPSERT TAGS
        # Only append tags in GetResponse but do not replace 'tags'!
        # TODO: This will be replaced by a more sophisticated thing because upsert can never 'clear' (set empty)
        #       a tag!!!
        tags = data.pop('tags', None)
        if tags:
            tags_payload = {'tags': tags}
            tags_upsert_result = self.getresponse_api_session.upsert_contact_tags(ext_id, tags_payload)
            assert len(tags) == len(tags_upsert_result.get('tags', [])), (
                "Upsert (add or update) of tags failed!")

        # Update the other contact data
        contact = self.getresponse_api_session.update_contact(ext_id, body=data)

        # WARNING: !!! We return the campaign object and not a dict !!!
        return contact

    def delete(self, ext_id):
        try:
            result = self.getresponse_api_session.delete_contact(ext_id)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))
        return result
