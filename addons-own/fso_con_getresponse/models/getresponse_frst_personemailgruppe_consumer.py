# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
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
@on_record_create(model_names=['frst.personemailgruppe'])
def create_personemailgruppe_bindings_for_all_backends(session, model_name, record_id, vals):

    # Skipp the binding creation because this is an 'import' from GetResponse
    if session.context.get('connector_no_export'):
        _logger.info("Skipp create_personemailgruppe_bindings_for_all_backends because connector_no_export in context:"
                     " '%s', '%s', '%s'" % (model_name, record_id, vals))
        return

    # Skipp the binding creation if the getresponse sync is disabled in the group of the personemailgruppe
    peg_record = session.env[model_name].browse([record_id])
    if not peg_record.zgruppedetail_id.sync_with_getresponse:
        _logger.debug("Skipp create_personemailgruppe_bindings_for_all_backends because sync is disabled in group:"
                      " '%s', '%s', '%s'" % (model_name, record_id, vals))
        return

    # Skipp the binding creation if the status of the peg record is wrong
    if not peg_record.state in ['subscribed', 'approved']:
        _logger.debug("Skipp create_personemailgruppe_bindings_for_all_backends because state is '%s':"
                      " '%s', '%s', '%s'" % (peg_record.state, model_name, record_id, vals))
        return


    # Create the binding
    _logger.info("create_personemailgruppe_bindings_for_all_backends: %s, %s, %s" % (model_name, record_id, vals))
    binding_model_obj = session.env['getresponse.frst.personemailgruppe']
    getresponse_backends = session.env['getresponse.backend'].search([])
    for backend in getresponse_backends:

        # Skipp the binding creation if it exists already
        existing = binding_model_obj.search([('odoo_id', '=', record_id), ('backend_id', '=', backend.id)], limit=1)
        if existing:
            _logger.error("Skipp create_personemailgruppe_bindings_for_all_backends on record creation because binding"
                          " exists!: '%s', '%s', '%s'" % (model_name, record_id, vals))
            return

        # Create a new binding
        if not existing:
            binding_vals = {'backend_id': backend.id, 'odoo_id': record_id}
            binding_record = binding_model_obj.create(binding_vals)
            _logger.info("Created binding for '%s' on record creation! (binding: %s %s, vals: %s)"
                         "" % (model_name, binding_record._name, binding_record.id, binding_vals)
                         )


# ------------------------------------------------------------
# Export new personemailgruppe bindings without an external id
# ------------------------------------------------------------
# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['getresponse.frst.personemailgruppe'])
def delay_export_personemailgruppe_on_create(session, model_name, record_id, vals):
    _logger.info("delay_export_personemailgruppe_on_create: %s, %s, %s" % (model_name, record_id, vals))

    # Skipp the export of the new binding because this is an 'import' from GetResponse
    if session.context.get('connector_no_export'):
        _logger.info("Skipp delay_export_personemailgruppe_on_create because connector_no_export in context:"
                     " '%s', '%s', '%s'" % (model_name, record_id, vals))
        return

    # Get the record
    record = session.env['getresponse.frst.personemailgruppe'].browse([record_id])

    # Skipp the export if it is already bound to an external id
    if record.getresponse_id:
        _logger.error("Skipp delay_export_personemailgruppe_on_create on bind record creation because external id"
                      " exists: '%s', '%s', '%s'" % (model_name, record_id, vals))
        return

    # Export the new binding to GetResponse
    consumer_export_binding(session, model_name, record_id, vals, delay=True)


# -------------------------------------------------
# Export personemailgruppe if relevant data changes
# -------------------------------------------------
# INFO: This is called AFTER the record write (but before the commit)
@on_record_write(model_names=['res.partner', 'frst.personemail', 'frst.personemailgruppe'])
def delay_export_personemailgruppe_on_update(session, model_name, record_id, vals):
    assert model_name in ['res.partner', 'frst.personemail', 'frst.personemailgruppe'], 'Unexpected model name!'

    # Skipp the export of the bindings because this is an 'import' from GetResponse
    # TODO: DO NOT SKIPP UPDATES TO OTHER 'RELATED' PEG BINDINGS _ WE MUST KNOW THE RECORD AND THE ID OF THE BINDING
    #       THAT WAS IMPORTED IN THE CONTEXT TO ONLY SUPPRESS SUBSEQUENT EXPORTS TO THE IMPORTED RECORD!!!
    if session.context.get('connector_no_export'):
        _logger.info("Skipp delay_export_personemailgruppe_on_update because connector_no_export in context:"
                     " '%s', '%s', '%s'" % (model_name, record_id, vals))
        return

    # Get all odoo field names from the custom field definitions
    watched_custom_fields_by_model = session.env['gr.custom_field'].watched_fields()

    # Get Watched fields
    watched_fields = []
    if model_name == 'res.partner':
        watched_fields = ['name', 'getresponse_tag_ids']
        if watched_custom_fields_by_model.get(model_name, False):
            watched_fields += watched_custom_fields_by_model[model_name]

    elif model_name == 'frst.personemail':
        watched_fields = ['email', 'partner_id', 'state']
        if watched_custom_fields_by_model.get(model_name, False):
            watched_fields += watched_custom_fields_by_model[model_name]

    elif model_name == 'frst.personemailgruppe':
        watched_fields = ['zgruppedetail_id', 'frst_personemail_id', 'state']
        if watched_custom_fields_by_model.get(model_name, False):
            watched_fields += watched_custom_fields_by_model[model_name]

    # Find the personemailgruppe binding records
    peg_bindings = []
    if any(f_name in vals for f_name in watched_fields):
        record = session.env[model_name].browse([record_id])
        # Find the subscription bindings
        if model_name == 'res.partner':
            peg_bindings = record.mapped('frst_personemail_ids.personemailgruppe_ids.getresponse_bind_ids')
        elif model_name == 'frst.personemail':
            peg_bindings = record.mapped('personemailgruppe_ids.getresponse_bind_ids')
        elif model_name == 'frst.personemailgruppe':
            peg_bindings = record.mapped('getresponse_bind_ids')

    # Export the personemailgruppe (subscription) data as contact to GetResponse
    # ATTENTION: We only export the record data for existing bindings! We do not create new bindings here!
    # HINT: The record may finally not be exported because of the peg state or the related group settings
    for binding_record in peg_bindings:
        consumer_export_binding(session, binding_record._name, binding_record.id, vals, delay=True)


# ATTENTION: Since cascade deletes are done in the database we have to watch the 'gr.tag' model also because
#            the deletion of the getresponse.gr.tag record is not done by the orm but by the database itself!
# @on_record_unlink(model_names=['gr.tag'])
# def delay_export_delete_of_gr_tag(session, model_name, record_id):
#     _logger.info("delay_export_delete_of_gr_tag: %s, %s" % (model_name, record_id))
#
#     if model_name == 'getresponse.gr.tag':
#         consumer_export_unlink_for_binding(session, model_name, record_id, delay=True)
#     else:
#         record = session.env[model_name].browse([record_id])
#         for binding_record in record.getresponse_bind_ids:
#             assert binding_record._name == 'getresponse.gr.tag', "Unexpected binding model!"
#             consumer_export_unlink_for_binding(session, binding_record._name, binding_record.id, delay=True)