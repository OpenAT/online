# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink

from .helper_consumer import prepare_binding, export_binding, export_delete


_logger = logging.getLogger(__name__)


# -----------------
# CONSUMER / EVENTS
# -----------------
# ATTENTION: This can only core odoo events - GetResponse Events must be covered by a controller that receives
#            HTTP request on record creation or update in GetResponse

# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['frst.personemailgruppe'])
def prepare_binding_on_contact_create(session, model_name, record_id, vals):
    """ Prepare a contact binding (without external id) for all backends (multiple backends possible)"""
    # We could get the binding model from session.env[model_name]._fields['getresponse_bind_ids'].comodel_name
    binding_model_name = 'getresponse.frst.personemailgruppe'
    unwrapped_record_id = record_id
    _logger.debug('CONSUMER: Prepare contact binding for binding model %s and frst.personemailgruppe id %s'
                  '' % (binding_model_name, unwrapped_record_id))
    prepare_binding(session, binding_model_name, unwrapped_record_id, vals)


# INFO: This is called AFTER the record create (but before the commit)
@on_record_create(model_names=['getresponse.frst.personemailgruppe'])
def export_binding_on_contact_binding_create(session, binding_model_name, binding_record_id, vals):
    """ Export a prepared contact binding (new binding without external id) """
    _logger.debug('CONSUMER: Export Contact binding ON CREATE %s, %s' % (binding_model_name, binding_record_id))
    export_binding(session, binding_model_name, binding_record_id, vals, delay=True)


# INFO: This is called AFTER the record write (but before the commit)
@on_record_write(model_names=['res.partner', 'frst.personemail', 'frst.personemailgruppe'])
def export_binding_on_contact_update(session, model_name, record_id, vals):
    """ Update the contact(s) in getresponse for all existing bindings (multiple backends possible) """
    # Get all odoo field names from the custom field definitions
    _logger.debug('CONSUMER: Export Contact binding ON UPDATE: model name: %s, record id: %s, vals: %s'
                  '' % (model_name, record_id, vals))
    watched_custom_fields_by_model = session.env['gr.custom_field'].watched_fields()

    # Get Watched fields
    watched_fields = []
    if model_name == 'res.partner':
        watched_fields = ['name', 'firstname', 'lastname', 'getresponse_tag_ids']
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

    # IF WATCHED FIELDS: Get binding records
    peg_bindings = []
    if any(f_name in vals for f_name in watched_fields):
        record = session.env[model_name].browse([record_id])
        # Find the contact bindings
        if model_name == 'res.partner':
            peg_bindings = record.mapped('frst_personemail_ids.personemailgruppe_ids.getresponse_bind_ids')
        elif model_name == 'frst.personemail':
            peg_bindings = record.mapped('personemailgruppe_ids.getresponse_bind_ids')
        elif model_name == 'frst.personemailgruppe':
            peg_bindings = record.mapped('getresponse_bind_ids')

    # EXPORT THE BINDING RECORDS (getresponse.frst.personemailgruppe to GetResponse)
    # ATTENTION: The record may finally not be exported because of the peg state or the related group settings.
    #            The filtering is done in the single record export in
    #            run() > _get_binding_record() > binder.get_bindings()
    for binding_record in peg_bindings:
        _logger.info('CONSUMER: Export Contact binding ON UPDATE: %s, %s' % (binding_record._name, binding_record.id))
        export_binding(session, binding_record._name, binding_record.id, vals, delay=True)
        # WARNING: It should be enough to export only one of the bindings since the export will export related bindings
        #          anyway.
        break


@on_record_unlink(model_names=['frst.personemailgruppe'])
def export_delete_on_contact_delete(session, model_name, record_id):
    """ Delete the contact(s) in getresponse for all existing bindings (multiple backends possible) """
    record = session.env[model_name].browse([record_id])
    # Get all binding records and export the delete
    for binding_record in record.getresponse_bind_ids:
        export_delete(session, binding_record._name, binding_record.id, delay=True)
