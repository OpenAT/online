# -*- coding: utf-8 -*-
import logging

from openerp.addons.connector.connector import Binder
from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink

from .helper_connector import get_environment, skipp_export_by_context

from .unit_export import export_record
from .unit_export_delete import export_delete_record
from .unit_binder import GetResponseBinder

_logger = logging.getLogger(__name__)


def prepare_binding(session, binding_model_name, unwrapped_record_id, vals, connector_no_export=False):
    _logger.info("CONSUMER: prepare binding for binding model: %s and unwrapped record id: %s"
                 "" % (binding_model_name, unwrapped_record_id))
    # Prevent export of binding at binding import! (recursion switch)
    # if skipp_export_by_context(session.context, binding_model_name, binding_record_id):
    if skipp_export_by_context(session.context):
        _logger.info("CONSUMER: SKIPP PREPARE BINDING for binding model: %s and unwrapped record id: %s"
                     "" % (binding_model_name, unwrapped_record_id))
        return

    # Search for the getresponse backend records
    getresponse_backends = session.env['getresponse.backend'].search([])
    for backend in getresponse_backends:

        # Get an connector environment
        env = get_environment(session, binding_model_name, backend.id)

        # Get the binder
        binder = env.get_connector_unit(GetResponseBinder)

        # ATTENTION: We use 'prepare_bindings()' to make sure 'get_unbound()' is used in case any limitations or
        #            constrains are added to get_unbound(). Check the binder definition for this model if unsure :)
        binder.prepare_bindings(domain=[('id', '=', unwrapped_record_id)], connector_no_export=connector_no_export)


def export_binding(session, binding_model_name, binding_record_id, vals, delay=True):
    _logger.info("CONSUMER: EXPORT binding %s %s" % (binding_model_name, binding_record_id))
    # Prevent export of binding at binding import! (recursion switch)
    # if skipp_export_by_context(session.context, binding_model_name, binding_record_id):
    if skipp_export_by_context(session.context):
        return

    if delay:
        export_record.delay(session, binding_model_name, binding_record_id)
    else:
        export_record(session, binding_model_name, binding_record_id)


def export_delete(session, binding_model_name, binding_record_id, delay=True):
    _logger.info("CONSUMER: EXPORT DELETE for binding %s, %s" % (binding_model_name, binding_record_id))
    # Prevent export of binding-deletion! (recursion switch)
    # if skipp_export_by_context(session.context, binding_model_name, binding_record_id):
    if skipp_export_by_context(session.context):
        _logger.info("CONSUMER: SKIPP EXPORT DELETE for binding %s, %s" % (binding_model_name, binding_record_id))
        return

    # Get the backend_id
    record = session.env[binding_model_name].browse([binding_record_id])
    backend_id = record.backend_id.id

    # Get the external id
    env = get_environment(session, binding_model_name, backend_id)
    binder = env.get_connector_unit(Binder)
    getresponse_id = binder.to_backend(binding_record_id)

    # Export the record delete
    if getresponse_id:
        if delay:
            export_delete_record.delay(session, binding_model_name, backend_id, getresponse_id)
        else:
            export_delete_record(session, binding_model_name, backend_id, getresponse_id)


