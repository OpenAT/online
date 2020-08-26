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
        string='GetResponse Connector Backend',
        required=True,
        readonly=True,
        ondelete='restrict'
    )
    odoo_id = fields.Many2one(
        comodel_name='gr.custom_field',
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

    # This constraint is very important for the multithreaded conflict resolution - needed in every binding model!
    _sql_constraints = [
        ('getresponse_uniq', 'unique(backend_id, getresponse_id)',
         'A binding already exists with the same GetResponse ID for this GetResponse backend (Account).'),
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
        """ Search records based on 'filters' and return a list of their ids """
        custom_fields = self.getresponse_api_session.get_custom_fields(params=params)
        return [cf.id for cf in custom_fields]

    def read(self, external_id, params=None):
        """ Returns the information of one record found by the external record id as a dict """
        try:
            custom_field = self.getresponse_api_session.get_custom_field(external_id, params=params)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))
        # WARNING: A dict() is expected! Right now 'custom_field' is a custom_field object!
        return custom_field.__dict__

    def search_read(self, params=None):
        """ Search records based on 'filters' and return their data """
        custom_fields = self.getresponse_api_session.get_custom_fields(params=params)
        # WARNING: A dict() is expected! Right now 'custom_field' is a custom_field object!
        return custom_fields.__dict__

    def create(self, data):
        custom_field = self.getresponse_api_session.create_custom_field(data)
        # WARNING: !!! We return the custom_field object an not a dict !!!
        return custom_field

    def write(self, external_id, data):
        try:
            custom_field = self.getresponse_api_session.update_custom_field(external_id, body=data)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))
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
        return result

