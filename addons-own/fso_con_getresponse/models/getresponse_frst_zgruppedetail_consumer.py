# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink

from .helper_consumer import prepare_binding, export_binding, export_delete


_logger = logging.getLogger(__name__)


# -----------------
# CONSUMER / EVENTS
# -----------------

# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['frst.zgruppedetail'])
def prepare_binding_on_campaign_create(session, model_name, record_id, vals):
    """ Prepare a campaign definition binding (without external id) for all backends (multiple backends possible)"""
    # We could get the binding model from session.env[model_name]._fields['getresponse_bind_ids'].comodel_name
    binding_model_name = 'getresponse.frst.zgruppedetail'
    unwrapped_record_id = record_id
    prepare_binding(session, binding_model_name, unwrapped_record_id, vals)


# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['getresponse.frst.zgruppedetail'])
def export_campaign_on_campaign_binding_create(session, binding_model_name, binding_record_id, vals):
    """ Export a prepared campaign definition binding (new binding without external id) """
    export_binding(session, binding_model_name, binding_record_id, vals, delay=True)


# INFO: This is called AFTER the record write (but before the commit)
@on_record_write(model_names=['frst.zgruppedetail'])
def export_binding_on_campaign_update(session, model_name, record_id, vals):
    """ Update the campaign definition(s) in getresponse for all existing bindings (multiple backends possible) """
    record = session.env[model_name].browse([record_id])
    # Get all binding records and export them
    for binding_record in record.getresponse_bind_ids:
        export_binding(session, binding_record._name, binding_record.id, vals, delay=True)


# DISABLED: Right now we do not support deletions of GetResponse Campaigns!
# @on_record_unlink(model_names=['frst.zgruppedetail'])
# def export_delete_on_campaign_delete(session, model_name, record_id):
#     """ Delete the campaign definition(s) in getresponse for all existing bindings (multiple backends possible) """
#     record = session.env[model_name].browse([record_id])
#     # Get all binding records and export the delete
#     for binding_record in record.getresponse_bind_ids:
#         export_delete(session, binding_record._name, binding_record.id, delay=True)
