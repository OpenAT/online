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
from getresponse.excs import NotFoundError

from openerp import models, fields

from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink
from openerp.addons.connector.exception import IDMissingInBackend

from .backend import getresponse
from .helper_consumer import consumer_export_binding, consumer_export_unlink_for_binding
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder

_logger = logging.getLogger(__name__)


# -----------------
# CONSUMER / EVENTS
# -----------------
# INFO: This is called AFTER the record create (but before the commit)
# TODO: Replace by generic method in helper_consumer.py
@on_record_create(model_names=['gr.custom_field'])
def create_gr_custom_field_bindings_for_all_backends(session, model_name, record_id, vals):
    if session.context.get('connector_no_export'):
        _logger.info("Skipp create_gr_custom_field_bindings_for_all_backends because connector_no_export in context:"
                     " '%s', '%s', '%s'" % (model_name, record_id, vals))
        return

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

