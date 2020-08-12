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
#     - CREATION OF BINDING RECORDS
#       create a binding record on record creation of the unwrapped model, might be done in the crud methods or
#       by consumer methods triggerd by @on_record_create or @on_record_write
#     - FIRING OF EVENTS TO START CONSUMERS
#       Call consumer functions on events like @on_record_create and alike
#
# The importers and exporters are in separate files!
# ----------------
import logging

from openerp import models, fields

from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink

from .backend import getresponse
from .helper_consumer import consumer_export_binding, consumer_export_unlink_for_binding
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder

_logger = logging.getLogger(__name__)


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseCustomField(models.Model):
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


class GetResponseGrCustomField(models.Model):
    _inherit = 'gr.custom_field'

    getresponse_bind_ids = fields.One2many(
        comodel_name='getresponse.gr.custom_field',
        inverse_name='odoo_id',
    )


# -----------------
# CONSUMER / EVENTS
# -----------------
# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['gr.custom_field'])
def create_gr_custom_field_bindings_for_all_backends(session, model_name, record_id, vals):
    _logger.warning("create_custom_field_bindings_for_all_backends: %s, %s, %s" % (model_name, record_id, vals))

    # TODO: Get the backend_field_name from the binder somehow ... egg chicken problem?
    binding_model_obj = session.env['getresponse.gr.custom_field']
    getresponse_backends = session.env['getresponse.backend'].search([])

    for backend in getresponse_backends:
        existing = binding_model_obj.search([('odoo_id', '=', record_id), ('backend_id', '=', backend.id)], limit=1)
        if not existing:
            binding_vals = {'backend_id': backend.id, 'odoo_id': record_id}
            binding_record = binding_model_obj.create(binding_vals)
            _logger.info("Created binding for '%s' before batch export! (binding: %s %s, vals: %s)"
                         "" % (model_name, binding_record._name, binding_record.id, binding_vals)
                         )


# ATTENTION: The model that inherits the base model will not trigger an write for all fields that are in the
#            inherits model: e.g. if we update 'getresponse.gr.custom_field'.gr_values only 'gr.custom_field' will
#            call the write method. That is why we need to add the model 'gr.custom_field' to @on_record_write.
# INFO: This is called AFTER the record create or write (but before the commit)
@on_record_create(model_names=['getresponse.gr.custom_field'])
@on_record_write(model_names=['getresponse.gr.custom_field', 'gr.custom_field'])
def delay_export_gr_custom_field(session, model_name, record_id, vals):
    _logger.warning("delay_export_custom_field: %s, %s, %s" % (model_name, record_id, vals))
    if model_name == 'getresponse.gr.custom_field':
        consumer_export_binding(session, model_name, record_id, vals, delay=True)
    else:
        record = session.env[model_name].browse([record_id])
        for binding_record in record.getresponse_bind_ids:
            assert binding_record._name == 'getresponse.gr.custom_field', "Unexpected binding model!"
            consumer_export_binding(session, binding_record._name, binding_record.id, vals, delay=True)


# ATTENTION: Since cascade deletes are done in the database we have to watch the 'gr.custom_field' model also because
#            the deletion of the getresponse.gr.custom_field record is not done by the orm but by the database itself!
@on_record_unlink(model_names=['getresponse.gr.custom_field', 'gr.custom_field'])
def delay_export_delete_of_gr_custom_field(session, model_name, record_id):
    _logger.warning("delay_export_delete_of_custom_field: %s, %s" % (model_name, record_id))
    if model_name == 'getresponse.gr.custom_field':
        consumer_export_unlink_for_binding(session, model_name, record_id, delay=True)
    else:
        record = session.env[model_name].browse([record_id])
        for binding_record in record.getresponse_bind_ids:
            assert binding_record._name == 'getresponse.gr.custom_field', "Unexpected binding model!"
            consumer_export_unlink_for_binding(session, binding_record._name, binding_record.id, delay=True)


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
        custom_field = self.getresponse_api_session.get_custom_field(external_id, params=params)
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
        custom_field = self.getresponse_api_session.update_custom_field(external_id, body=data)
        # WARNING: !!! We return the custom_field object and not a dict !!!
        return custom_field

    def delete(self, external_id):
        """
        Returns:
            bool: True for success, False otherwise
        """
        result = self.getresponse_api_session.delete_custom_field(external_id)
        return result


