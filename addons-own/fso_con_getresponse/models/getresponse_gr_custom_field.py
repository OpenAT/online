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
import logging
from getresponse.excs import NotFoundError

from openerp import models, fields

from openerp.addons.connector.exception import IDMissingInBackend

from .backend import getresponse
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder

_logger = logging.getLogger(__name__)


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseGrCustomFieldBinding(models.Model):
    _name = 'getresponse.gr.custom_field'
    _inherits = {'gr.custom_field': 'odoo_id'}
    _description = 'GetResponse Custom Field Definition Binding'

    backend_id = fields.Many2one(
        comodel_name='getresponse.backend',
        index=True,
        string='GetResponse Connector Backend',
        required=True,
        readonly=True,
        ondelete='restrict'
    )
    odoo_id = fields.Many2one(
        comodel_name='gr.custom_field',
        inverse_name='getresponse_bind_ids',
        index=True,
        string='GetResponse Custom Field Definition',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    getresponse_id = fields.Char(
        string='GetResponse Custom Field ID',
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


class GrCustomFieldGetResponse(models.Model):
    _inherit = 'gr.custom_field'

    getresponse_bind_ids = fields.One2many(
        comodel_name='getresponse.gr.custom_field',
        inverse_name='odoo_id',
    )


# ----------------
# CONNECTOR BINDER
# ----------------
@getresponse
class CustomFieldBinder(GetResponseBinder):
    _model_name = ['getresponse.gr.custom_field']

    _bindings_domain = [('field_id', '!=', False)]

    # Make sure only mapped custom field definitions will get a prepared binding
    # HINT: get_unbound() is used by prepare_bindings() which is used in the batch exporter > prepare_binding_records()
    #       and in helper_consumer.py > prepare_binding_on_record_create() to filter out records where no binding
    #       should be prepared (created) for export.
    def get_unbound(self, domain=None, limit=None):
        domain = domain if domain else []
        domain += self._bindings_domain
        unbound = super(CustomFieldBinder, self).get_unbound(domain=domain, limit=limit)
        return unbound

    # Make sure only bindings with a mapped custom field definition are returned
    # HINT: get_bindings() is used in single record exporter run() > _get_binding_record() to filter and validate
    #       the binding record
    def get_bindings(self, domain=None, limit=None):
        domain = domain if domain else []
        domain += self._bindings_domain
        bindings = super(CustomFieldBinder, self).get_bindings(domain=domain, limit=limit)
        return bindings

# -----------------
# CONNECTOR ADAPTER
# -----------------
# The Adapter is a subclass of an ConnectorUnit class. The ConnectorUnit Object holds information about the
# connector_env, the backend, the backend_record and about the connector session
@getresponse
class CustomFieldAdapter(GetResponseCRUDAdapter):
    """
    ATTENTION: read() and search_read() will return a dict and not the getresponse_record itself but
               create() and write() will return a getresponse object from the getresponse-python lib!
    """

    _model_name = 'getresponse.gr.custom_field'
    _getresponse_model = 'custom-fields'

    def search(self, params=None):
        """ Search records based on 'filters'

        Returns: list of custom field ids
        """
        custom_fields = self.getresponse_api_session.get_custom_fields(params=params)
        return [cf.id for cf in custom_fields]

    def read(self, external_id, params=None):
        """ Returns the information of one record found by the external record id as a dict """

        try:
            custom_field = self.getresponse_api_session.get_custom_field(external_id, params=params)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not custom_field:
            raise ValueError('No data returned from GetResponse for custom field %s! Response: %s'
                             '' % (external_id, custom_field))

        # WARNING: A dict() is expected! Right now 'custom_field' is a custom_field object!
        return custom_field.__dict__

    def search_read(self, params=None):
        """ Search records based on 'filters' and return their data

        Returns: list of custom fields as dicts
        """
        custom_fields = self.getresponse_api_session.get_custom_fields(params=params)
        # WARNING: A dict() is expected! Right now 'custom_field' is a list of custom_field object!
        return [cf.__dict__ for cf in custom_fields]

    def create(self, data):
        custom_field = self.getresponse_api_session.create_custom_field(data)
        assert custom_field, "Could not create custom field in GetResponse!"
        # WARNING: !!! We return the custom_field object an not a dict !!!
        return custom_field

    def write(self, external_id, data):

        try:
            custom_field = self.getresponse_api_session.update_custom_field(external_id, body=data)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not custom_field:
            raise ValueError('No data was written to GetResponse for custom field %s! Response: %s'
                             '' % (external_id, custom_field))

        # WARNING: !!! We return the custom_field object and not a dict !!!
        return custom_field

    def delete(self, external_id):
        """
        Returns:
            bool: True for success, False otherwise
        """
        try:
            result = self.getresponse_api_session.delete_custom_field(external_id)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not result:
            raise ValueError('Custom field %s could not be deleted in GetResponse! Response: %s'
                             '' % (external_id, result))

        return result


