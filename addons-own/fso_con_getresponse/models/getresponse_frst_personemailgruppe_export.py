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

from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.exception import IDMissingInBackend

from .helper_connector import get_environment
from .backend import getresponse
from .unit_export import BatchExporter, GetResponseExporter
from .unit_export_delete import GetResponseDeleteExporter
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
        assert bind_record.getresponse_id == self.getresponse_id, (
            "bind_record.getresponse_id and self.getresponse_id do not match!")
        if not self.current_getresponse_record:
            try:
                self.current_getresponse_record = self.backend_adapter.read(self.getresponse_id)
            except IDMissingInBackend:
                if bind_record.getresponse_id:
                    raise IDMissingInBackend('GetResponse ID %s no longer exits!' % self.getresponse_id)
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

        # Current odoo tags
        current_odoo_tags = partner.getresponse_tag_ids
        tags_binder = self.binder_for('getresponse.gr.tag')
        odoo_tags_ext_ids = []
        for tag in current_odoo_tags:
            getresponse_tag_id = tags_binder.to_backend(tag.id, wrap=True)
            assert getresponse_tag_id, (
                    "Could not find the getresponse id for tag (gr.tag) %s for contact (personemailgruppe) %s "
                    "" % (tag.id, bind_record.id))
            odoo_tags_ext_ids.append(getresponse_tag_id)

        # Directly export the odoo tag list for GetResponse contact record creation
        if not bind_record.getresponse_id:
            return {'tags': [{'tagId': tag_id} for tag_id in odoo_tags_ext_ids]}

        # Get current getresponse tag list
        current_getresponse_record = self._get_current_getresponse_record(bind_record)
        getresponse_tags = current_getresponse_record.raw_data.get('tags', {})
        getresponse_tag_ids = [tag.get('tagId') for tag in getresponse_tags]

        # Combine the current getresponse tags with the tags in odoo
        result = list(set(odoo_tags_ext_ids) | set(getresponse_tag_ids))

        # REMOVE TAGS THAT WHERE UNAMBIGUOUSLY REMOVED IN ODOO SINCE THE LAST SYNC
        if bind_record.compare_data:
            last_sync_cmp_data = json.loads(bind_record.compare_data, encoding='utf8')
            if 'tags' in last_sync_cmp_data:
                last_sync_tags = last_sync_cmp_data.get('tags')
                last_sync_tag_ids = [tag.get('tagId') for tag in last_sync_tags]
                for index, tag_id in enumerate(result):
                    if tag_id in last_sync_tag_ids and tag_id not in odoo_tags_ext_ids:
                        result.pop(index)

        # Return the final tag list
        return {'tags': [{'tagId': tag_id} for tag_id in result]}

    # ATTENTION: A CONTACT 'UPDATE' WOULD REPLACE ALL CURRENT CUSTOM FIELDS WITH THE CUSTOM FIELDS GIVEN HERE!
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
        odoo_mapped_custom_field_data = {}
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
            # Append the custom field data to odoo_mapped_custom_field_data
            odoo_mapped_custom_field_data[getresponse_custom_field_id] = value

        # Directly export the odoo custom field data for GetResponse contact record creation
        if not bind_record.getresponse_id:
            return {'customFieldValues': [{'customFieldId': key, 'value': value}
                                          for key, value in odoo_mapped_custom_field_data.iteritems()]}

        # Get the current GetResponse custom field data of the contact
        current_getresponse_record = self._get_current_getresponse_record(bind_record)
        gr_custom_field_values = current_getresponse_record.raw_data.get('customFieldValues', {})
        gr_custom_field_data = {f['customFieldId']: f['value'] for f in gr_custom_field_values}

        # Odoo field values takes precedence on export over the GetResponse custom field values
        result = gr_custom_field_data
        result.update(odoo_mapped_custom_field_data)

        # REMOVE FORMER MAPPED CUSTOM FIELDS
        odoo_cf_prefix = custom_fields_obj._gr_field_prefix
        field_exporter = self.unit_for(GetResponseExporter, model='getresponse.gr.custom_field')
        field_definitions = field_exporter.backend_adapter.search_read(self.f_id)
        cf_key_to_name = {cfd['customFieldId']: cfd['name'] for cfd in field_definitions.raw_data}
        for f_id in result:
            if f_id not in odoo_mapped_custom_field_data:
                if f_id not in odoo_mapped_custom_field_data and cf_key_to_name[f_id].startswith(odoo_cf_prefix):
                    result.pop(f_id)

        # REMOVE CUSTOM FIELDS THAT WHERE UNAMBIGUOUSLY REMOVED IN ODOO SINCE THE LAST SYNC
        if bind_record.compare_data:
            last_sync_cmp_data = json.loads(bind_record.compare_data, encoding='utf8')
            if 'customFieldValues' in last_sync_cmp_data:
                last_custom_field_values = last_sync_cmp_data['customFieldValues']
                last_sync_field_data = {f['customFieldId']: f['value'] for f in last_custom_field_values}
            for f_id in result:
                if f_id in last_sync_field_data and f_id not in odoo_mapped_custom_field_data:
                    result.pop(f_id)

        return {'customFieldValues': [{'customFieldId': key, 'value': value} for key, value in result.iteritems()]}


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

    # Export missing campaigns, tag definitions and custom field definitions
    def _export_dependencies(self):
        # ------------------------
        # EXPORT MISSING CAMPAIGNS
        # ------------------------
        campaigns = self.session.env['frst.zgruppedetail'].sudo().search([('sync_with_getresponse', "!=", False)])

        cmp_binding_model = getattr(campaigns, self.binder._inverse_binding_ids_field)._name
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
        boolean_result = self.backend_adapter.create(create_data)
        assert boolean_result, ("EXPORT: Could not schedule the contact creation in getresponse! (%s, %s)"
                                "" % (self.binding_record._name, self.binding_record.id))

        # Log the export
        _logger.info("EXPORT: Contact creation was scheduled in GetResponse for binding '%s', '%s'"
                     "" % (self.binding_record._name, self.binding_record.id))

        # ADD THE RETURNED GETRESPONSE_RECORD TO SELF
        self.getresponse_record = 'DELAYED CONTACT CREATION IN GETRESPONSE'

        # UPDATE THE EXTERNAL ID FOR THE BINDING UPDATE LATER ON IN .run() > _update_binding_after_export()
        self.getresponse_id = 'DELAYED CONTACT CREATION IN GETRESPONSE'
        
        # Create a delayed binding job with some retries (1, 2, 4, 8 minutes)
        contact_email = create_data['email']
        contact_campaing_id = create_data['campaign']['campaignId']
        eta = 10
        delayed_contact_binding_and_import.delay(self.session, self.model._name, self.binding_id,
                                                 contact_email, contact_campaing_id,
                                                 eta=eta, max_retries=7)

        # Log the delayed binding
        _logger.info("EXPORT: A delayed contact binding and import was scheduled in '%s's for '%s', '%s', '%s', '%s'"
                     "" % (eta, self.binding_record._name, self.binding_record.id, contact_email, contact_campaing_id))

    def _update_binding_after_export(self, map_record, sync_data=None):
        if self.getresponse_id == 'DELAYED CONTACT CREATION IN GETRESPONSE':
            _logger.info(
                "EXPORT: SKIPP _update_binding_after_export() because the contact creation in GetResponse is delayed!"
                " (%s, %s)" % (self.binding_record._name, self.binding_record.id)
            )
        else:
            return super(ContactExporter, self)._update_binding_after_export(map_record, sync_data=sync_data)


# -----------------------------
# SINGLE RECORD DELETE EXPORTER
# -----------------------------
@getresponse
class ContactDeleteExporter(GetResponseDeleteExporter):
    _model_name = ['getresponse.frst.personemailgruppe']


@job(default_channel='root.getresponse', retry_pattern={1: 10, 2: 60, 3: 10 * 60})
def delayed_contact_binding_and_import(session, model_name, binding_id, contact_email, contact_campaing_id,
                                       eta=10, max_retries=7):
    # Get the odoo binding record
    binding = session.env[model_name].browse(binding_id)

    # Get an connector environment
    env = get_environment(session, model_name, binding.backend_id.id)

    # Get the importer
    contact_importer = env.get_connector_unit(ContactImporter)

    # Search for the contact in GetResponse
    contact_ids = contact_importer.backend_adapter.search(getresponse_campaign_ids=[contact_campaing_id],
                                                          email=contact_email)
    assert len(contact_ids) == 1, ("Contact for delayed binding not found in GetResponse! '%s', '%s', '%s', '%s'"
                                   "" % (model_name, binding_id, contact_email, contact_campaing_id))

    # Get and check the external id of the contact
    getresponse_contact_id = contact_ids[0]
    assert getresponse_contact_id and isinstance(getresponse_contact_id, basestring), (
        'GetResponse Contact ID must be a string!')

    # UPDATE THE BINDING WITH THE GETRESPONSE CONTACT ID BEFORE IMPORT
    contact_importer.binder.bind(getresponse_contact_id, binding_id,
                                 sync_data='DELAYED CONTACT BINDING',
                                 compare_data='DELAYED CONTACT BINDING')
    _logger.info("Binding '%s', '%s', was bound to '%s' before import for delayed contact creation!"
                 "" % (model_name, binding_id, getresponse_contact_id))

    # IMPORT THE CONTACT FROM GETRESPONSE
    contact_importer.run(getresponse_contact_id)
