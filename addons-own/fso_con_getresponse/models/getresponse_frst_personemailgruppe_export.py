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

from .helper_connector import get_environment
from .backend import getresponse
from .unit_export import BatchExporter, GetResponseExporter
from .unit_export_delete import GetResponseDeleteExporter

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
    _model_name = 'getresponse.frst.personemailgruppe'

    def _map_children(self, bind_record, attr, model):
        pass

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

        partner_gr_tags = partner.getresponse_tag_ids

        # TODO: Get the current tags list from getresponse
        #       Get the tags of the last sync from sync_data of the binding
        #       Get a set of changed tags since the last sync (fson_removed, fson_added, gr_removed, gr_added)
        #       Prepare the new final list of tags
        # TODO: If we call importer._map_data() this will run the mappper on the import side which may again load
        #       the odoo record on the export side ... make sure there is no recursion going on here!
        #       But i guess the import mapper may not need the export mapper but just go straight for the odoo data?
        # importer = env.get_connector_unit(GetResponseImporter)
        # gr_raw_data = importer._map_data()
        # mapped_update_data = importer._update_data(map_record)

        if not partner_gr_tags:
            return

        tags_binder = self.binder_for('getresponse.gr.tag')
        getresponse_tag_ids = []
        for tag in partner_gr_tags:
            getresponse_tag_id = tags_binder.to_backend(tag.id, wrap=True)
            assert getresponse_tag_id, (
                    "Could not find the getresponse id for tag (gr.tag) %s for contact (personemailgruppe) %s "
                    "" % (tag.id, bind_record.id)
            )
            getresponse_tag_ids.append({"tagId": getresponse_tag_id})

        return {'tags': getresponse_tag_ids}

    # ATTENTION: A CONTACT 'UPDATE' WOULD REPLACE ALL CURRENT CUSTOM FIELDS WITH THE CUSTOM FIELDS GIVEN HERE!
    # TODO: We only import or export values for custom field definitions that are linked to an odoo field!
    #       But to be able to remove custom field values from Getresponse it might be better to import all
    #       custom field values - even the ones we can not map - to be able to prepare a complete list of fields
    #       for the export and the import. we may store this additional values to an extra field in the binding.
    @mapping
    def custom_field_values(self, bind_record):
        # HINT: Make sure the lang of the bind_record and the fields is the lang in the backend and of the custom field
        #       This should be the case already since helper_connector.py get_environment() should handle this!
        # Get all mapped custom fields:
        mapped_custom_fields = self.session.env['gr.custom_field'].sudo().search([('field_id', "!=", False)])

        if not mapped_custom_fields:
            return

        # TODO: Get the current custom field values from getresponse
        #       Get the custom field values of the last sync from sync_data of the binding
        #       Get a set of changed field values since the last sync (fson_removed, fson_added, gr_removed, gr_added)
        #       Prepare the new final list of custom field values

        bind_record_model_name = bind_record._name
        peg_binder = self.binder_for(bind_record_model_name)
        openerp_field_name = peg_binder._openerp_field

        personemailgruppe = getattr(bind_record, openerp_field_name)
        personemail = personemailgruppe.frst_personemail_id
        partner = personemail.partner_id

        custom_field_values = []
        custom_field_binder = self.binder_for('getresponse.gr.custom_field')

        for custom_field in mapped_custom_fields:
            # Get the external id of the custom field
            getresponse_custom_field_id = custom_field_binder.to_backend(custom_field.id, wrap=True)
            assert getresponse_custom_field_id, (
                    "Could not find the getresponse id for custom field (gr.custom_field) %s "
                    "for contact (personemailgruppe) %s " % (custom_field.id, bind_record.id)
            )

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

            # ATTENTION: Multiple values are currently NOT supported (so one2many and many2many is not supported yet)
            value = '' if not custom_field_value else custom_field_value
            value = value if isinstance(value, basestring) else str(custom_field_value)

            # ATTENTION: custom field values must always be in a list
            custom_field_values.append(
                {
                    "customFieldId": getresponse_custom_field_id,
                    "value": [value]
                 }
            )

        return {'customFieldValues': custom_field_values}


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

    #  TODO: FOLLOWUP: I really think an import would be better - this could update the sync_data and other
    #                  stuff also!!!
    def delayed_contact_binding_after_export(self, binding_id, contact_email, contact_campaing_id):
        self.binding_id = binding_id
        self.binding_record = self._get_binding_record()

        contact_ids = self.backend_adapter.search(getresponse_campaign_ids=[contact_campaing_id], email=contact_email)

        if len(contact_ids) == 1:
            contact_id = contact_ids[0]
            assert contact_id and isinstance(contact_id, basestring), 'GetResponse Contact ID must be a string!'

            # Read the contact from GetResponse
            contact_dict = self.backend_adapter.read(contact_id)

            if contact_dict and contact_dict.get('id', '') == contact_id:
                self.getresponse_id = contact_id
                _logger.info("Delayed binding for contact with external id %s! binding id %s"
                             "" % (contact_id, self.binding_id))
                self.binder.bind(contact_id, self.binding_id, sync_data='DELAYED CONTACT BINDING')

    # Export missing tag and custom field definitions
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
    def create(self, map_record, fields=None):
        create_data = self._create_data(map_record, fields=fields)
        if not create_data:
            return _('Nothing to export.')

        # Special check on data before export
        self._validate_create_data(create_data)

        boolean_result = self.backend_adapter.create(create_data)
        assert boolean_result, "Could not create the contact! (binding_id: %s)" % self.binding_id

        # ADD THE RETURNED GETRESPONSE_RECORD TO SELF
        self.getresponse_record = 'DELAYED CONTACT CREATION IN GETRESPONSE'

        # UPDATE THE EXTERNAL ID FOR THE BINDING UPDATE LATER ON IN .run()
        self.getresponse_id = 'DELAYED CONTACT CREATION IN GETRESPONSE'
        
        # Create a delayed binding job with some retries (1, 2, 4, 8 minutes)
        # TODO: FOLLOWUP: I really think an import would be better - this could update the sync_data and other
        #                 stuff also!!!
        contact_email = create_data['email']
        contact_campaing_id = create_data['campaign']['campaignId']
        delayed_contact_binding.delay(self.session, self.model._name, self.binding_id,
                                      contact_email, contact_campaing_id,
                                      eta=10, max_retries=7)

    def _bind_after_export(self):
        if self.getresponse_id == 'DELAYED CONTACT CREATION IN GETRESPONSE':
            _logger.info(
                "Could not bind contact after export because the contact creation in GetResponse is delayed!"
                " (binding_id: %s)" % self.binding_id
            )
        else:
            return super(ContactExporter, self)._bind_after_export()


# -----------------------------
# SINGLE RECORD DELETE EXPORTER
# -----------------------------
@getresponse
class ContactDeleteExporter(GetResponseDeleteExporter):
    _model_name = ['getresponse.frst.personemailgruppe']


#  TODO: FOLLOWUP: I really think an import would be better - this could update the sync_data and other
#                  stuff also!!!
@job(default_channel='root.getresponse', retry_pattern={1: 5, 2: 10, 3: 2 * 60})
def delayed_contact_binding(session, model_name, binding_id, contact_email, contact_campaing_id,
                            eta=10, max_retries=7):
    # Get the odoo binding record
    record = session.env[model_name].browse(binding_id)

    # Get an connector environment
    env = get_environment(session, model_name, record.backend_id.id)

    # Get the exporter
    exporter = env.get_connector_unit(ContactExporter)

    # Run the delayed binding
    exporter.delayed_contact_binding_after_export(binding_id, contact_email, contact_campaing_id)
