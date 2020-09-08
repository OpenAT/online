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
from openerp.addons.connector.session import ConnectorSession

from .backend import getresponse
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder
from .unit_export import export_record
from .unit_import import import_record

from .getresponse_frst_personemailgruppe_export import contact_export_batch
from .getresponse_frst_personemailgruppe_import import contact_import_batch

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

    compare_data = fields.Char(
        string='Last synchronization data to compare',
        readonly=True)

    # ATTENTION: !!! THE 'getresponse_uniq' CONSTRAIN MUST EXISTS FOR EVERY BINDING MODEL !!!
    # TODO: Check if the backend_uniq constrain makes any problems for the parallel processing of jobs
    _sql_constraints = [
        ('getresponse_uniq', 'unique(backend_id, getresponse_id)',
         'A binding already exists with the same GetResponse ID for this GetResponse backend (Account).'),
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A binding already exists for this odoo record and this GetResponse backend (Account).'),
    ]

    # ---------------------
    # CONTACTS SYNC BUTTONS
    # ---------------------
    @api.multi
    def export_getresponse_contact_direct(self):
        """ Export Contact Binding (personemailgruppe) for enabled Campaigns (zgruppedetail) to GetResponse """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for binding in self:
            export_record(session, binding._name, binding.backend_id.id)

    @api.multi
    def import_getresponse_contact_direct(self):
        """ Import Contact Binding (personemailgruppe) for enabled Campaigns (zgruppedetail) from GetResponse """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for binding in self:
            if binding.getresponse_id:
                import_record(session, binding._name, binding.backend_id.id, binding.getresponse_id)


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
    def search(self, getresponse_campaign_ids=None, name=None, email=None, custom_fields=None,
               subscriber_types=('subscribed',), **kwargs):
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
        :param subscriber_types: tuple
            format: ('subscribed', 'undelivered', 'removed', 'unconfirmed')

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
                                                                 subscriber_types=subscriber_types,
                                                                 **kwargs)
        return [contact.id for contact in contacts]

    def read(self, ext_id, attributes=None):
        """ Returns the information of one record found by the external record id as a dict """
        try:
            contact = self.getresponse_api_session.get_contact(ext_id, params=attributes)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not contact:
            raise ValueError('No data returned from GetResponse for contact %s! Response: %s'
                             '' % (ext_id, contact))

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
        return [c.__dict__ for c in contacts]

    def create(self, data):
        """ Scedules a Contact creation in GetResponse

        Returns:
            bool: True for success, False otherwise
        """
        # ATTENTION: The contact may not be created immediately by GetResponse - Therefore we will only get a
        #            boolean result. Therefore we can not bind the contact immediately!!!
        boolean_result = self.getresponse_api_session.create_contact(data)
        assert boolean_result, "Could not create contact in GetResponse!"
        return boolean_result

    # ATTENTION: PLEASE CHECK 'PITFALLS' COMMENT AT THE START OF THE FILE!
    def write(self, ext_id, data):
        # Update the contact in GetResponse
        # ATTENTION: !!! This will replace the custom fields and the tags completely in GetResponse !!!

        try:
            contact = self.getresponse_api_session.update_contact(ext_id, body=data)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not contact:
            raise ValueError('No data was written to GetResponse for contact %s! Response: %s'
                             '' % (ext_id, contact))

        # WARNING: !!! We return the contact object and not a dict !!!
        return contact

    def delete(self, ext_id):
        """
        Returns:
            bool: True for success, False otherwise
        """
        try:
            result = self.getresponse_api_session.delete_contact(ext_id)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not result:
            raise ValueError('Contact %s could not be deleted in GetResponse! Response: %s'
                             '' % (ext_id, result))

        return result
