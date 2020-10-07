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
from .unit_binder import GetResponseBinder
from .unit_adapter import GetResponseCRUDAdapter


_logger = logging.getLogger(__name__)


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseGrTagBinding(models.Model):
    _name = 'getresponse.gr.tag'
    _inherits = {'gr.tag': 'odoo_id'}
    _description = 'GetResponse Tag Definition Binding'

    backend_id = fields.Many2one(
        comodel_name='getresponse.backend',
        index=True,
        string='GetResponse Connector Backend',
        required=True,
        readonly=True,
        ondelete='restrict'
    )
    odoo_id = fields.Many2one(
        comodel_name='gr.tag',
        inverse_name='getresponse_bind_ids',
        index=True,
        string='GetResponse Tag Definition',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    getresponse_id = fields.Char(
        string='GetResponse Tag ID',
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


class GrTagGetResponse(models.Model):
    _inherit = 'gr.tag'

    # ATTENTION: INVERSE FIELD MUST BE CALLED 'getresponse_bind_ids' !!!
    getresponse_bind_ids = fields.One2many(
        comodel_name='getresponse.gr.tag',
        inverse_name='odoo_id',
    )


# ----------------
# CONNECTOR BINDER
# ----------------
# You may override binder methods here if special processing is needed for this model
@getresponse
class TagBinder(GetResponseBinder):
    _model_name = ['getresponse.gr.tag']


# -----------------
# CONNECTOR ADAPTER
# -----------------
# The Adapter is a subclass of an ConnectorUnit class. The ConnectorUnit Object holds information about the
# connector_env, the backend, the backend_record and about the connector session
@getresponse
class TagAdapter(GetResponseCRUDAdapter):
    """
    ATTENTION: read() and search_read() will return a dict and not the getresponse_record itself but
               create() and write() will return a getresponse object from the getresponse-python lib!
    """

    _model_name = 'getresponse.gr.tag'
    _getresponse_model = 'tags'

    def search(self, params=None):
        """ Search records based on 'filters' and return a list of their external ids """
        tags = self.getresponse_api_session.get_tags(params=params)
        return [tag.id for tag in tags]

    def read(self, external_id, attributes=None):
        """ Returns the information of one record found by the external record id as a dict """
        try:
            tag = self.getresponse_api_session.get_tag(external_id, params=attributes)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not tag:
            raise ValueError('No data returned from GetResponse for tag %s! Response: %s'
                             '' % (external_id, tag))

        # WARNING: A dict() is expected! Right now 'tag' is a tag object!
        return tag.__dict__

    def search_read(self, params=None):
        """ Search records based on 'filters' and return their data """
        tags = self.getresponse_api_session.get_tags(params=params)
        # WARNING: A dict() is expected! Right now 'tag' is a tag object!
        return [tag.__dict__ for tag in tags]

    def create(self, data):
        tag = self.getresponse_api_session.create_tag(data)
        assert tag, "Could not create tag in GetResponse!"
        # WARNING: !!! We return the tag object an not a dict !!!
        return tag

    def write(self, external_id, data):
        try:
            tag = self.getresponse_api_session.update_tag(external_id, body=data)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not tag:
            raise ValueError('No data was written to GetResponse for tag %s! Response: %s'
                             '' % (external_id, tag))

        # WARNING: !!! We return the tag object and not a dict !!!
        return tag

    def delete(self, external_id):
        """
        Returns:
            bool: True for success, False otherwise
        """
        try:
            result = self.getresponse_api_session.delete_tag(external_id)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))

        if not result:
            raise ValueError('Tag %s could not be deleted in GetResponse! Response: %s'
                             '' % (external_id, result))

        return result


