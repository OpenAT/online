# -*- coding: utf-8 -*-
import logging

from openerp.addons.connector.connector import Binder
from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink

from .helper_connector import get_environment

from .unit_export import export_record
from .unit_export_delete import export_delete_record

_logger = logging.getLogger(__name__)


# TODO: Write this as an generic method to be called by the consumers!
def consumer_create_bindings_for_all_backends(session, model_name, record_id, vals):
    """ This is used in combination with @on_record_create to create bindings on record create """

    # TODO: Get the backend_field_name from the binder somehow ... egg chicken problem?
    binding_model_obj = session.env['getresponse.gr.tag']
    getresponse_backends = session.env['getresponse.backend'].search([])

    for backend in getresponse_backends:
        existing = binding_model_obj.search([('odoo_id', '=', record_id), ('backend_id', '=', backend.id)], limit=1)
        if not existing:
            binding_vals = {'backend_id': backend.id, 'odoo_id': record_id}
            binding_record = binding_model_obj.create(binding_vals)
            _logger.info("Created binding for '%s' before batch export! (binding: %s %s, vals: %s)"
                         "" % (model_name, binding_record._name, binding_record.id, binding_vals)
                         )


def consumer_export_binding(session, binding_model_name, binding_record_id, vals, delay=True):
    """ Export a binding record direct or delayed (by connector job)

    Called from a binding record:
    'model_name' and 'record_id' must be for the binding model
    e.g.:  model_name = getresponse.frst.zgruppedetail
    """
    if session.context.get('connector_no_export'):
        _logger.info('Skipp consumer_export_binding() because connector_no_export in context: %s, %s'
                     '' % (binding_model_name, binding_record_id))
        return

    fields = vals.keys()

    if delay:
        export_record.delay(session, binding_model_name, binding_record_id, fields=fields)
    else:
        export_record(session, binding_model_name, binding_record_id, fields=fields)


def consumer_export_bindings_of_record(session, unwrapped_model_name, unwrapped_record_id, vals, delay=True):
    """ Export all the bindings of a regular record direct or delayed (by connector job)

    Called from a regular record:
    'model_name' and 'record_id' must be for the unwrapped model (so not the binding model)
    e.g.:  model_name = frst.zgruppedetail
    """
    if session.context.get('connector_no_export'):
        _logger.info('Skipp consumer_export_bindings_of_record() because connector_no_export in context: %s, %s'
                     '' % (unwrapped_model_name, unwrapped_record_id))
        return

    regular_record = session.env[unwrapped_model_name].browse(unwrapped_record_id)
    fields = vals.keys()

    for binding in regular_record.getresponse_bind_ids:
        if delay:
            export_record.delay(session, binding._model._name, binding.id, fields=fields, delay=True)
        else:
            export_record(session, binding._model._name, binding.id, fields=fields, delay=True)


def consumer_export_unlink_for_binding(session, binding_model_name, binding_record_id, delay=True):
    """ Export the unlink (deletion) a binding record direct or delayed (by connector job)

    Called from a binding record:
    'model_name' and 'record_id' must be for the binding model
    e.g.:  model_name = getresponse.frst.zgruppedetail
    """
    record = session.env[binding_model_name].browse([binding_record_id])

    # TODO: Get the backend_field_name from the binder somehow ... egg chicken problem?
    #backend_field_name = record._backend_field
    backend_id = record.backend_id.id

    env = get_environment(session, binding_model_name, backend_id)

    binder = env.get_connector_unit(Binder)
    getresponse_id = binder.to_backend(binding_record_id)

    if getresponse_id:
        if delay:
            export_delete_record.delay(session, binding_model_name, backend_id, getresponse_id)
        else:
            export_delete_record(session, binding_model_name, backend_id, getresponse_id)
