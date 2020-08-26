# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging
from getresponse.excs import NotFoundError

from openerp import models, fields

from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink
from openerp.addons.connector.exception import IDMissingInBackend

from .backend import getresponse
from .helper_consumer import prepare_binding, export_binding, export_delete
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder

_logger = logging.getLogger(__name__)


# -----------------
# CONSUMER / EVENTS
# -----------------

# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['gr.tag'])
def prepare_binding_on_tag_create(session, model_name, record_id, vals):
    """ Prepare a tag definition binding (without external id) for all existing backend records """
    prepare_binding(session, model_name, record_id, vals)


# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['getresponse.gr.tag'])
def export_tag_on_tag_binding_create(session, binding_model_name, binding_record_id, vals):
    """ Export a prepared tag definition binding (new binding without external id) """
    export_binding(session, binding_model_name, binding_record_id, vals, delay=True)


# INFO: This is called AFTER the record write (but before the commit)
@on_record_write(model_names=['gr.tag'])
def export_binding_on_tag_update(session, model_name, record_id, vals):
    """ Update the tag definition(s) in getresponse for all existing bindings (multiple backends possible) """
    record = session.env[model_name].browse([record_id])
    for binding_record in record.getresponse_bind_ids:
        export_binding(session, binding_record._name, binding_record.id, vals, delay=True)


@on_record_unlink(model_names=['frst.personemailgruppe'])
def export_delete_on_tag_delete(session, model_name, record_id):
    """ Delete the tag definition(s) in getresponse for all existing bindings (multiple backends possible) """
    record = session.env[model_name].browse([record_id])
    for binding_record in record.getresponse_bind_ids:
        export_delete(session, binding_record._name, binding_record.id, delay=True)