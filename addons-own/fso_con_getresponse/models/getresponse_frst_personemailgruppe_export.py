# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

# !!!!!!!!!
# PITFALLS:
# !!!!!!!!!
# - The getresponse-python lib will return objects! Sometimes GetResponse will not return all fields of an object!
#   Therefore it may appear that a field is 'unset' or False just because it was not returned by GetResponse!
#   There are two ways to check if a field was not returned or was returned but empty:
#     1. If the field value is False it was returned but empty - if it is Null it was not returned
#     2. Check if the field is in raw_data['kwargs'] ! This is the raw response data from GetResponse!
# - If you update a contact (POST to /contact/id) 'tags' and 'customFieldValues' will REPLACE all the existing TAGS
#   and/or custom fields !!! So make sure the contact data in FS-Online is 'up-to-date' with GetResponse before
#   exporting tags or custom fields!

import logging
import json
from datetime import datetime, timedelta

from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.exception import IDMissingInBackend, RetryableJobError

from .helper_connector import get_environment
from .helper_related_action import unwrap_binding

from .backend import getresponse

from .unit_export import BatchExporter, GetResponseExporter
from .unit_export_delete import GetResponseDeleteExporter, export_delete_record
from .unit_import import import_record

from .getresponse_frst_personemailgruppe_import import ContactImporter

_logger = logging.getLogger(__name__)


# -----------------------
# CONNECTOR EXPORT MAPPER
# -----------------------
@getresponse
class ContactExportMapper(ExportMapper):
    """ Map all the fields of the odoo bind_record to the GetResponse API field names.

    ATTENTION: !!! FOR THE EXPORT WE MUST USE THE FIELD NAMES OF THE GET RESPONSE API !!!

               When we import data the client lib will return a campaign object. The data of campaign is stored
               in the objects attributes. The pitfall is that the object attributes will follow python conventions so
               the GetResponse 'languageCode' is the attribute campaign.language_code if we read objects from GR.

               BUT for the export to GetResponse (update or write) we need the prepare the API "raw data" for the
               request!
    """
    def __init__(self, connector_env):
        super(ContactExportMapper, self).__init__(connector_env)
        self.current_getresponse_record = None

    _model_name = 'getresponse.frst.personemailgruppe'

    def _map_children(self, bind_record, attr, model):
        pass

    def _get_current_getresponse_record(self, bind_record):
        if not bind_record.getresponse_id:
            return None

        if not self.current_getresponse_record:
            try:
                exporter = self.unit_for(GetResponseExporter)
                self.current_getresponse_record = exporter.backend_adapter.read(bind_record.getresponse_id)
            except IDMissingInBackend:
                if bind_record.getresponse_id:
                    raise IDMissingInBackend('GetResponse ID %s no longer exits!' % bind_record.getresponse_id)
            except Exception as e:
                raise e

        return self.current_getresponse_record

    # ATTENTION: !!! FOR THE EXPORT WE MUST USE THE RAW FIELD NAMES OF THE GET RESPONSE API !!!

    @mapping
    def campaign(self, bind_record):
        zgruppedetail = bind_record.zgruppedetail_id
        campaign_binder = self.binder_for('getresponse.frst.zgruppedetail')
        getresponse_campaing_id = campaign_binder.to_backend(zgruppedetail.id, wrap=True)
        assert getresponse_campaing_id, (
                "Could not find the getresponse id for campaign (zgruppedetail) %s for contact (personemailgruppe) %s "
                "" % (zgruppedetail.id, bind_record.id)
        )
        return {'campaign': {'campaignId': getresponse_campaing_id}}

    @mapping
    def email(self, bind_record):
        personemail = bind_record.frst_personemail_id
        email = personemail.email
        return {'email': email}

    # ATTENTION: 'name' ist NOT required for contact creation!
    @mapping
    def name(self, bind_record):
        partner = bind_record.frst_personemail_id.partner_id
        name = partner.name
        return {'name': name}

    # ATTENTION: A CONTACT 'UPDATE' WOULD REPLACE ALL CURRENT TAGS WITH THE TAGS GIVEN HERE!
    @mapping
    def tags(self, bind_record):
        partner = bind_record.frst_personemail_id.partner_id

        # CURRENT ODOO TAGS
        # -----------------
        current_odoo_tags = partner.getresponse_tag_ids
        tags_binder = self.binder_for('getresponse.gr.tag')
        odoo_tags_ext_ids = []
        for tag in current_odoo_tags:
            getresponse_tag_id = tags_binder.to_backend(tag.id, wrap=True)
            assert getresponse_tag_id, (
                    "Could not find the getresponse id for tag (gr.tag) %s for contact (personemailgruppe) %s "
                    "" % (tag.id, bind_record.id))
            odoo_tags_ext_ids.append(getresponse_tag_id)

        # -----------------------------------
        # "DO NOT MERGE EXTERNAL DATA" SWITCH
        # -----------------------------------
        if hasattr(self.options, 'no_external_data'):
            payload = {'tags': [{'tagId': tag_id} for tag_id in odoo_tags_ext_ids]}
            return payload

        # GET GETRESPONSE TAGS
        # --------------------
        current_getresponse_record = self._get_current_getresponse_record(bind_record)
        getresponse_tags = current_getresponse_record['tags'] if current_getresponse_record else []
        getresponse_tag_ids = [tag['tagId'] for tag in getresponse_tags]

        # APPEND THE CURRENT GETRESPONSE TAGS WITH THE TAGS IN ODOO
        # ----------------------------------------------------------
        set_odoo_tags_ext_ids = set(odoo_tags_ext_ids)
        set_getresponse_tag_ids = set(getresponse_tag_ids)
        combined_tags = list(set_odoo_tags_ext_ids | set_getresponse_tag_ids)
        if len(combined_tags) != len(set_odoo_tags_ext_ids):
            _logger.info("EXPORT MAPPER: odoo tags '%s'" % set_odoo_tags_ext_ids)
            _logger.info("EXPORT MAPPER: GR tags '%s'" % set_getresponse_tag_ids)
            _logger.info("EXPORT MAPPER: combined tags '%s'" % combined_tags)

        # REMOVE TAGS THAT WHERE UNAMBIGUOUSLY REMOVED IN ODOO SINCE THE LAST SYNC
        # ------------------------------------------------------------------------
        # TODO: We may get all related bindings here and generate the complete list to not loose any data
        # HINT: This would only remove tags that are still in GR but where removed in odoo
        # HINT: We do not remove GetResponse Tags here - If only changes in GetResponse where made since the last
        #       sync we would do an import already instead of the export!
        #       The danger here is that odoo may set tags in GR again that are already removed in GR if data
        #       was changed in both system since the last export (FRST WINS)
        if bind_record.compare_data:
            last_sync_cmp_data = json.loads(bind_record.compare_data, encoding='utf8')
            if 'tags' in last_sync_cmp_data:
                last_sync_tags = last_sync_cmp_data.get('tags')
                last_sync_tag_ids = [tag.get('tagId') for tag in last_sync_tags]
                for index, tag_id in enumerate(combined_tags):
                    if tag_id in last_sync_tag_ids and tag_id not in odoo_tags_ext_ids:
                        _logger.info("EXPORT MAPPER: TAG %s UNAMBIGUOUSLY REMOVED IN ODOO" % tag_id)
                        combined_tags.pop(index)

        # Return the final tag list
        payload = {'tags': [{'tagId': tag_id} for tag_id in combined_tags]}
        return payload

    # HINT: A GR-API CONTACT 'UPDATE' WILL REPLACE ALL CURRENT CUSTOM FIELDS WITH THE CUSTOM FIELDS GIVEN HERE!
    @mapping
    def custom_field_values(self, bind_record):
        # HINT: Make sure the lang of the bind_record and the fields is the lang in the backend and of the custom field
        #       This should be the case already since helper_connector.py get_environment() should handle this!
        # Get all mapped custom fields:
        custom_fields_obj = self.session.env['gr.custom_field']
        mapped_custom_fields = custom_fields_obj.sudo().search([('field_id', "!=", False)])

        # If there are no mapped custom fields we will not change the custom fields of the contact in GetResponse!
        if not mapped_custom_fields:
            return

        # Get the unwrapped record field name
        bind_record_model_name = bind_record._name
        peg_binder = self.binder_for(bind_record_model_name)
        openerp_field_name = peg_binder._openerp_field

        # Get the odoo records that belong to the GetResponse Contact
        personemailgruppe = getattr(bind_record, openerp_field_name)
        personemail = personemailgruppe.frst_personemail_id
        partner = personemail.partner_id

        # Get the odoo custom field data
        current_odoo_mapped_field_data = {}
        custom_field_binder = self.binder_for('getresponse.gr.custom_field')
        for custom_field in mapped_custom_fields:
            # Get the external id of the custom field
            getresponse_custom_field_id = custom_field_binder.to_backend(custom_field.id, wrap=True)
            assert getresponse_custom_field_id, (
                    "Could not find the getresponse id for custom field (gr.custom_field) %s "
                    "for contact (personemailgruppe) %s " % (custom_field.id, bind_record.id))
            # Get the 'Getresponse value' from the record with the custom field model
            cf_odoo_field_model = custom_field.field_model_name
            if cf_odoo_field_model == personemailgruppe._name:
                custom_field_value = custom_field.record_to_gr_value(personemailgruppe)
            elif cf_odoo_field_model == personemail._name:
                custom_field_value = custom_field.record_to_gr_value(personemail)
            elif cf_odoo_field_model == partner._name:
                custom_field_value = custom_field.record_to_gr_value(partner)
            else:
                raise ValueError("The model '%s' is not supported for getresponse custom fields!" % cf_odoo_field_model)
            # Convert the value to a string
            # ATTENTION: Multiple values are currently NOT supported (so one2many and many2many is not supported yet)
            value = '' if not custom_field_value else custom_field_value
            value = value if isinstance(value, basestring) else str(custom_field_value)
            # Append the custom field data to current_odoo_mapped_field_data
            current_odoo_mapped_field_data[getresponse_custom_field_id] = value

        # -----------------------------------
        # "DO NOT MERGE EXTERNAL DATA" SWITCH
        # -----------------------------------
        # !!! PARTNER DATA MERGE DISABLED TEMPORARILY BECAUSE OF GETRESPONSE ERROR !!!
        _logger.warning("GR-CUSTOM-FIELD-DATA-MERGE IS DISABLED TEMPORARILY BECAUSE OF ERROR IN GETRESPONSE!")
        # if hasattr(self.options, 'no_external_data'):
        if True:
            payload = {'customFieldValues': [{'customFieldId': key,
                                              'value': val if isinstance(val, list) else [val]}
                                             for key, val in current_odoo_mapped_field_data.iteritems() if val]}
            return payload

        # GET THE CURRENT GETRESPONSE CUSTOM FIELD DATA OF THE CONTACT
        # ------------------------------------------------------------
        current_getresponse_record = self._get_current_getresponse_record(bind_record)
        gr_custom_field_values = current_getresponse_record['custom_field_values'] if current_getresponse_record else []
        gr_custom_field_data = {f['customFieldId']: f['value'] for f in gr_custom_field_values}

        # REMOVE FORMER MAPPED ODOO CUSTOM FIELDS FROM CURRENT GETRESPONSE FIELD DATA
        # ---------------------------------------------------------------------------
        # TODO: We may get all related bindings here and generate the complete list to not loose any data
        # HINT: This would only remove custom fields that are no longer mapped in odoo or where removed in odoo
        odoo_cf_prefix = custom_fields_obj._gr_field_prefix
        field_exporter = self.unit_for(GetResponseExporter, model='getresponse.gr.custom_field')
        field_definitions = field_exporter.backend_adapter.search_read()
        cf_key_to_name = {cfd['id']: cfd['name'] for cfd in field_definitions}
        for f_id in gr_custom_field_data:
            if f_id not in current_odoo_mapped_field_data and cf_key_to_name[f_id].startswith(odoo_cf_prefix):
                _logger.info("EXPORT MAPPER: Custom field '%s' was removed because it is no longer mapped" % f_id)
                gr_custom_field_data.pop(f_id)

        # COMBINE CURRENT ODOO CUSTOM FIELDS WITH CURRENT GETRESPONSE CUSTOM FIELDS
        # -------------------------------------------------------------------------
        # TODO: We may get all related bindings here and generate the complete list to not loose any data
        # HINT: Odoo field values takes precedence on export over the GetResponse custom field values
        # HINT: We do not remove GetResponse CF data here - If only changes in GetResponse where made since the last
        #       sync we would do an import already instead of the export!
        #       The danger here is that odoo may set cf data again that was already removed in GR if data
        #       was changed in both system since the last export (FRST WINS)
        gr_only_custom_fields = {key: val for key, val in gr_custom_field_data.iteritems()
                                 if key not in current_odoo_mapped_field_data}
        if gr_only_custom_fields:
            _logger.info("EXPORT MAPPER: GR-only custom fields '%s' where merged for export" % gr_only_custom_fields)
        result = gr_custom_field_data
        result.update(current_odoo_mapped_field_data)

        # REMOVE CUSTOM FIELDS THAT WHERE UNAMBIGUOUSLY REMOVED IN ODOO SINCE THE LAST SYNC
        # ---------------------------------------------------------------------------------
        # HINT: This would only remove custom fields that are still in GR but where removed in odoo
        if bind_record.compare_data:
            last_sync_cmp_data = json.loads(bind_record.compare_data, encoding='utf8')
            if 'customFieldValues' in last_sync_cmp_data:
                last_sync_custom_field_values = last_sync_cmp_data['customFieldValues']
                last_sync_fields = {f['customFieldId']: f['value'] for f in last_sync_custom_field_values}
                for f_id in result:
                    # Remove fields that existed in the last sync but are no longer mapped (or existing) in odoo
                    if f_id in last_sync_fields and f_id not in current_odoo_mapped_field_data:
                        _logger.info("EXPORT MAPPER: CUSTOM FIELD %s UNAMBIGUOUSLY REMOVED IN ODOO" % f_id)
                        result.pop(f_id)

        # RETURN THE COMBINED RESULT
        # --------------------------
        # HINT: We remove fields if the val is missing because GetResponse may not accept custom fields
        #       with empty values! (... if val)
        payload = {'customFieldValues': [{'customFieldId': key,
                                          'value': val if isinstance(val, list) else [val]}
                                         for key, val in result.iteritems() if val]}
        return payload


# ---------------------------------------------------------------------------------------------------------------------
# EXPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------

# --------------
# BATCH EXPORTER
# --------------
@getresponse
class ContactBatchExporter(BatchExporter):
    _model_name = ['getresponse.frst.personemailgruppe']


@job(default_channel='root.getresponse')
def contact_export_batch(session, model_name, backend_id, domain=None, fields=None, delay=False, **kwargs):
    """ Prepare the batch export of contacts to GetResponse """
    connector_env = get_environment(session, model_name, backend_id)

    # Get the exporter connector unit
    batch_exporter = connector_env.get_connector_unit(ContactBatchExporter)

    # Start the batch export
    batch_exporter.batch_run(domain=domain, fields=fields, delay=delay, **kwargs)


# ----------------------
# SINGLE RECORD EXPORTER
# ----------------------
# In this class we could alter the generic GetResponse export sync flow for 'getresponse.frst.personemailgruppe'
# HINT: We could overwrite all the methods from the shared GetResponseExporter here if needed!
@getresponse
class ContactExporter(GetResponseExporter):
    _model_name = ['getresponse.frst.personemailgruppe']

    _base_mapper = ContactExportMapper

    def _get_binding_record(self):
        binding = super(ContactExporter, self)._get_binding_record()

        # DELAYED CONTACT CREATION IN PROGRESS
        if binding and binding.sync_data == 'DELAYED CREATION IN GETRESPONSE':
            raise RetryableJobError("EXPORT: The binding '%s', '%s' can not be exported yet because we still wait for "
                                    "the delayed contact binding to finish!" % (binding._name, binding.id))

        # DELETE BINDINGS (GR contacts) THAT ARE NO LONGER VALID BASED ON THE BINDER get_bindings() METHOD
        elif not binding and self.binding_id:
            blocked_binding = self.model.browse([self.binding_id])
            if len(blocked_binding) == 1 and blocked_binding.getresponse_id:
                _logger.warning("EXPORT: The binding '%s', '%s', 'odoo id %s', 'gr id %s' was filtered out by "
                                "get_bindings() and therefore is no longer valid! A delete job will be created to "
                                "delete the contact from GetResponse!"
                                "" % (binding._name, binding.id, binding.odoo_id, binding.getresponse_id))
                export_delete_record.delay(self.session, blocked_binding._name, self.backend_record.id,
                                           blocked_binding.getresponse_id)

        return binding

    # Export missing campaigns, tag definitions and custom field definitions
    def _export_dependencies(self):
        # ------------------------
        # EXPORT MISSING CAMPAIGNS
        # ------------------------
        campaigns = self.session.env['frst.zgruppedetail'].sudo().search([('sync_with_getresponse', "!=", False)])

        if campaigns:
            cmp_binding_model = getattr(campaigns[0], self.binder._inverse_binding_ids_field)._name
            cmp_binder = self.binder_for(cmp_binding_model)

            for cmp in campaigns:
                cmp_external_id = cmp_binder.to_backend(cmp.id, wrap=True)
                if not cmp_external_id:
                    self._export_dependency(cmp)

        # ------------------------------
        # EXPORT MISSING TAG DEFINITIONS
        # ------------------------------
        unwrapped_record = self.binder.unwrap_binding(self.binding_record, browse=True)
        partner_gr_tags = unwrapped_record.frst_personemail_id.partner_id.getresponse_tag_ids

        if partner_gr_tags:
            tag_binding_model = getattr(partner_gr_tags[0], self.binder._inverse_binding_ids_field)._name
            tags_binder = self.binder_for(tag_binding_model)

            # Export tag definitions with missing binding or existing binding without an external id
            for tag_definition in partner_gr_tags:
                tag_external_id = tags_binder.to_backend(tag_definition.id, wrap=True)
                # Export this prepared binding for the tag definition before the contact (peg) export
                if not tag_external_id:
                    self._export_dependency(tag_definition)

        # ----------------------------------------------
        # EXPORT MISSING MAPPED CUSTOM FIELD DEFINITIONS
        # ----------------------------------------------
        mapped_custom_fields = self.session.env['gr.custom_field'].sudo().search([('field_id', "!=", False)])

        if mapped_custom_fields:
            cf_binding_model = getattr(mapped_custom_fields[0], self.binder._inverse_binding_ids_field)._name
            cf_binder = self.binder_for(cf_binding_model)

            for custom_field_definition in mapped_custom_fields:
                cf_external_id = cf_binder.to_backend(custom_field_definition.id, wrap=True)
                if not cf_external_id:
                    self._export_dependency(custom_field_definition)

    # ATTENTION: On contact creation GetResponse will only return a boolean because the real contact creation may be
    #            delayed. Therefore we can not bind the record directly after the contact creation but need to
    #            create a delayed job to search for the new contact and bind it later!
    def create(self, create_data=None):
        # --------------------------------------------
        # SCHEDULE THE CONTACT CREATION IN GETRESPONSE
        # --------------------------------------------
        boolean_result = self.backend_adapter.create(create_data)
        assert boolean_result, ("EXPORT: Could not schedule the contact creation in getresponse! (%s, %s)"
                                "" % (self.binding_record._name, self.binding_record.id))

        # Log the export
        _logger.info("EXPORT: Contact creation was scheduled in GetResponse for binding '%s', '%s'"
                     "" % (self.binding_record._name, self.binding_record.id))

        # UPDATE self.getresponse_record FOR THE BINDING UPDATE LATER ON IN .run() > _update_binding_after_export()
        # ATTENTION: This will be checked in unit_export.py > run()
        self.getresponse_record = 'DELAYED CREATION IN GETRESPONSE'

        # ---------------------------------------------------------
        # SCHEDULE AN ODOO JOB TO BIND AND IMPORT THE CONTACT LATER
        # ---------------------------------------------------------
        contact_email = create_data['email']
        contact_campaing_id = create_data['campaign']['campaignId']
        eta = 60*2
        delayed_contact_binding_and_import.delay(self.session, self.model._name, self.binding_id,
                                                 contact_email, contact_campaing_id,
                                                 eta=eta, max_retries=7)

        # Log the delayed binding
        _logger.info("EXPORT: A delayed contact binding was scheduled in '%s's for '%s', '%s', email: '%s',"
                     " campaign_id: '%s'"
                     "" % (eta, self.binding_record._name, self.binding_record.id, contact_email, contact_campaing_id))

    def _update_binding_after_export(self, map_record, sync_data=None, compare_data=None):
        if self.getresponse_record == 'DELAYED CREATION IN GETRESPONSE':
            self.binding_record.with_context(connector_no_export=True).write(
                {'sync_data': 'DELAYED CREATION IN GETRESPONSE',
                 'compare_data': 'DELAYED CREATION IN GETRESPONSE'})
        else:
            super(ContactExporter, self)._update_binding_after_export(map_record,
                                                                      sync_data=sync_data,
                                                                      compare_data=compare_data)

    def skipp_after_export_methods(self):
        if self.binding_record and self.binding_record.sync_data == 'DELAYED CREATION IN GETRESPONSE':
            return ("EXPORT: Skipp all after export methods for delayed contact binding '%s', '%s'"
                    "" % (self.binding_record._name, self.binding_record.id))
        else:
            return super(ContactExporter, self).skipp_after_export_methods()

    # ATTENTION: !!! Changes are no longer really written to the records because dry_run=True !!!
    #            It is still enabled for some time to search for bugs in the comparison of the data but
    #            this method may be removed entirely in the future!
    def _check_data_in_gr_after_export(self, *args, **kwargs):
        _logger.info("EXPORT: _check_data_in_gr_after_export()")
        # Update the odoo records with the getresponse record data after the export because data may have been
        # merged or added by the export mapper or getresponse
        binding = self.binding_record

        # Read the data from the getresponse record
        # HINT: This should be already updated in GR since the API update call was already done!
        contact_importer = self.unit_for(ContactImporter)
        contact_importer.binding_record = binding
        contact_importer.getresponse_id = binding.getresponse_id
        contact_importer.getresponse_record = contact_importer._get_getresponse_data()
        contact_importer.map_record = contact_importer._get_map_record()
        update_data = contact_importer.map_record.values()

        # Update the odoo record
        # HINT: _update of the importer sets: binding_no_export = binding.with_context(connector_no_export=True)
        #       so the update of this odoo record will not trigger an export to GR again!
        # ATTENTION: !!! Changes are no longer really written to the records because dry_run=True !!!
        result = contact_importer._update(self.binding_record, update_data, dry_run=True)

        # Log the update and return the result
        _logger.info('DRY-RUN-ONLY (data will NOT be written to records!): '
                     '_check_data_in_gr_after_export (for binding %s, %s) after export!' % (binding._name, binding.id))
        return result

    def _export_related_bindings(self, *args, **kwargs):
        # Export other Contact bindings of this res.partner
        # HINT: The export will be skipped if the last sync compare data matches the current payload
        contact_binding = self.binding_record
        partner = contact_binding.frst_personemail_id.partner_id
        all_contact_bindings = partner.mapped('frst_personemail_ids.personemailgruppe_ids.getresponse_bind_ids')
        related_contact_bindings = all_contact_bindings - contact_binding
        for related_binding in related_contact_bindings:
            _logger.info("Export related contact binding '%s', '%s' to '%s' AFTER EXPORT OF '%s', '%s'!"
                         "" % (related_binding._name, related_binding.id, related_binding.getresponse_id,
                               contact_binding._name, contact_binding.id))
            self.run(related_binding.id, skip_export_related_bindings=True)
            
    def run(self, binding_id, *args, **kwargs):

        # RECORD REMOVED IN GETRESPONSE HANDLING
        try:
            return super(ContactExporter, self).run(binding_id, *args, **kwargs)
        except IDMissingInBackend as e:
            # Expire the personemailgruppe since it was removed in GetResponse
            if self.binding_record and self.binding_record.getresponse_id:
                peg = self.binder.unwrap_binding(self.binding_record, browse=True)
                if len(peg) == 1:
                    msg = ('CONTACT ID %s NOT FOUND IN GETRESPONSE! Expiring frst.personemailgruppe %s !'
                           '' % (self.binding_record.getresponse_id, peg.id))
                    _logger.warning(msg)
                    yesterday = datetime.now() - timedelta(days=1)
                    # Expire the personemailgruppe
                    peg.with_context(connector_no_export=True).write({'gueltig_bis': yesterday})
                    # Delete the binding record
                    self.binding_record.with_context(connector_no_export=True).unlink()
                    return msg
            raise e
        except Exception as e:
            raise e


# -----------------------------
# SINGLE RECORD DELETE EXPORTER
# -----------------------------
@getresponse
class ContactDeleteExporter(GetResponseDeleteExporter):
    _model_name = ['getresponse.frst.personemailgruppe']


# -----------------------
# DELAYED CONTACT BINDING
# -----------------------
@job(default_channel='root.getresponse', retry_pattern={1: 60, 2: 60 * 2, 3: 60 * 10})
@related_action(action=unwrap_binding)
def delayed_contact_binding_and_import(session, model_name, binding_id, contact_email, contact_campaing_id,
                                       eta=10, max_retries=7):
    _logger.info("DELAYED BINDING: Start import for model name: %s, binding_id %s, contact_email %s, campaign id %s"
                 "" % (model_name, binding_id, contact_email, contact_campaing_id))
    # Get the odoo binding record
    binding = session.env[model_name].browse(binding_id)

    # SKIPP THE DELAYED BINDING IF ALREADY BOUND (ALREADY IMPORTED)
    # -------------------------------------------------------------
    if binding.getresponse_id:
        return

    # Get an connector environment
    env = get_environment(session, model_name, binding.backend_id.id)

    # Get the importer
    contact_importer = env.get_connector_unit(ContactImporter)

    # Search for the contact in GetResponse
    contact_ids = contact_importer.backend_adapter.search(getresponse_campaign_ids=[contact_campaing_id],
                                                          email=contact_email,
                                                          subscriber_types=('subscribed',))
    if not contact_ids:
        raise RetryableJobError("DELAYED BINDING: Contact for delayed binding not found in GetResponse!"
                                " model name: %s, binding_id %s, contact_email %s, campaign id %s"
                                "" % (model_name, binding_id, contact_email, contact_campaing_id))
    elif len(contact_ids) > 1:
        raise ValueError("DELAYED BINDING: Contact for delayed binding found MULTIPLE TIMES in GetResponse!"
                         " model name: %s, binding_id %s, contact_email %s, campaign id %s"
                         "" % (model_name, binding_id, contact_email, contact_campaing_id))

    # Get and check the external id of the contact
    getresponse_contact_id = contact_ids[0]
    assert getresponse_contact_id and isinstance(getresponse_contact_id, basestring), (
        'GetResponse Contact ID must be a string!')

    # UPDATE THE BINDING WITH THE GETRESPONSE CONTACT ID BEFORE IMPORT
    # ----------------------------------------------------------------
    # ATTENTION: Do not use binder.bind or you will erase important binding data!
    _logger.info("DELAYED BINDING: Binding '%s', '%s', will be bound to '%s' before import of contact!"
                 "" % (model_name, binding_id, getresponse_contact_id))
    binding.with_context(connector_no_export=True).write({
        'getresponse_id': getresponse_contact_id,
        'sync_data': False,
        'compare_data': False,
    })

    # Check the external id was written to the binding
    assert binding.getresponse_id == getresponse_contact_id, (
        "DELAYED BINDING: External id of binding '%s', '%s' could not be updated!" % (model_name, binding_id))

    # COMMIT SO WE KEEP THE EXTERNAL ID IN ANY CIRCUMSTANCES.
    binding.env.cr.commit()

    # Log the result
    result = ("DELAYED BINDING: Binding '%s', '%s', was bound to '%s' before import!"
              "" % (model_name, binding_id, getresponse_contact_id))
    _logger.info(result)

    # Create an import job
    # --------------------
    _logger.info("DELAYED BINDING: Create an import job for binding '%s', '%s'"
                 "" % (model_name, binding_id))
    import_record.delay(session, model_name, binding.backend_id.id, getresponse_contact_id,
                        skip_import_related_bindings=True,
                        skip_export_related_bindings=True,
                        eta=eta)

    return result
