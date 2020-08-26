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

from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink

from .helper_consumer import prepare_binding, export_binding, export_delete


_logger = logging.getLogger(__name__)


# -----------------
# CONSUMER / EVENTS
# -----------------
# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['gr.custom_field'])
def prepare_binding_on_custom_field_create(session, model_name, record_id, vals):
    """ Prepare a custom field definition binding (without external id) for all existing backend records """
    prepare_binding(session, model_name, record_id, vals)


# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['getresponse.gr.custom_field'])
def export_custom_field_on_custom_field_binding_create(session, binding_model_name, binding_record_id, vals):
    """ Export a prepared custom field definition binding (new binding without external id) """
    export_binding(session, binding_model_name, binding_record_id, vals, delay=True)


# INFO: This is called AFTER the record write (but before the commit)
@on_record_write(model_names=['gr.custom_field'])
def export_binding_on_custom_field_update(session, model_name, record_id, vals):
    """ Update the custom field definition(s) in getresponse for all existing bindings (multiple backends possible) """
    record = session.env[model_name].browse([record_id])
    for binding_record in record.getresponse_bind_ids:
        export_binding(session, binding_record._name, binding_record.id, vals, delay=True)


@on_record_unlink(model_names=['frst.personemailgruppe'])
def export_delete_on_custom_field_delete(session, model_name, record_id):
    """ Delete the custom field definition(s) in getresponse for all existing bindings (multiple backends possible) """
    record = session.env[model_name].browse([record_id])
    for binding_record in record.getresponse_bind_ids:
        export_delete(session, binding_record._name, binding_record.id, delay=True)
