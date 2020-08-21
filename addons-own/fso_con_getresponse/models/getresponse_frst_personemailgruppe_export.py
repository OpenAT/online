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

    # TODO: We need to make sure that the campaign exists and is in sync BEFORE we export a contact
    #       Therefore we need to implement _run.()._export_dependencies() or make sure campaigns are
    #       always exported first
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

    # TODO: Maybe we can find a more sophisticated method for the firstname and lastname stuff?
    #       e.g. if we have firstname and lastname parts in the custom fields we could split them like we need it ...
    # ATTENTION: 'name' ist NOT required for contact creation!
    @mapping
    def name(self, bind_record):
        partner = bind_record.frst_personemail_id.partner_id
        name = partner.name
        return {'name': name}

    # TODO: We need to make sure that all tag definitions exists and are in sync BEFORE we export a contact
    #       Therefore we many need to implement _run.()._export_dependencies() or make sure tag definitions are
    #       always exported first
    # ATTENTION: A CONTACT 'UPDATE' WOULD REPLACE ALL CURRENT TAGS WITH THE TAGS GIVEN HERE!
    @mapping
    def tags(self, bind_record):
        partner = bind_record.frst_personemail_id.partner_id

        partner_gr_tags = partner.getresponse_tag_ids

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
    @mapping
    def custom_field_values(self, bind_record):
        # HINT: Make sure the lang of the bind_record and the fields is the lang in the backend and of the custom field
        #       This should be the case already since helper_connector.py get_environment() should handle this!
        # Get all mapped custom fields:
        mapped_custom_fields = self.session.env['gr.custom_field'].sudo().search([('field_id', "!=", False)])

        if not mapped_custom_fields:
            return

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

    # CREATE BINDING RECORDS BEFORE THE BATCH EXPORT
    def batch_run_create_binding_records(self):
        odoo_regular_model_name = self.binder.unwrap_model()

        assert self.model._name == 'getresponse.frst.personemailgruppe', (
            "Model 'getresponse.frst.personemailgruppe' expected!"
        )

        # SEARCH FOR CONTACTS IN ENABLED CAMPAIGN-BINDINGS NOT LINKED TO A BINDING RECORD
        # Get all enabled campaign bindings
        campaigns = self.session.env['getresponse.frst.zgruppedetail'].sudo().search(
            [('sync_with_getresponse', '=', True)]
        )
        campaign_contacts = campaigns.mapped('frst_personemailgruppe_ids')
        # TODO: Consider status of personemailgruppe (contact) also
        contacts_without_binding = campaign_contacts.filtered(lambda r: not r.getresponse_bind_ids)

        # CREATE A BINDING BEFORE THE EXPORT
        for contact in contacts_without_binding:
            binding_vals = {
                self.binder._backend_field: self.backend_record.id,
                self.binder._openerp_field: contact.id
            }
            binding = self.env[self.model._name].create(binding_vals)
            _logger.info("Created binding for '%s' before batch export! (binding: %s %s, vals: %s)"
                         "" % (odoo_regular_model_name, binding._name, binding.id, binding_vals)
                         )

    # ONLY EXPORT CONTACT-BINDINGS WHERE THE CAMPAIGN IS ENABLED FOR SYNCING!
    # TODO: Consider status of personemailgruppe (contact) also
    def batch_run_search_binding_records(self, domain=None):
        odoo_binding_model_name = self.model._name
        assert odoo_binding_model_name == 'getresponse.frst.personemailgruppe', (
            "Model 'getresponse.frst.personemailgruppe' expected!"
        )

        odoo_binding_model_obj = self.env['getresponse.frst.personemailgruppe']

        if not domain:
            binding_records = odoo_binding_model_obj.search([('zgruppedetail_id.sync_with_getresponse', '=', True)])
        else:
            domain_records = odoo_binding_model_obj.search(domain)
            binding_records = domain_records.filtered(lambda r: r.zgruppedetail_id.sync_with_getresponse)

        return binding_records


@job(default_channel='root.getresponse')
def contact_export_batch(session, model_name, backend_id, domain=None, fields=None, delay=False, **kwargs):
    """ Prepare the batch export of custom field definitions to GetResponse """
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

    # ONLY EXPORT CONTACT-BINDINGS WHERE THE CAMPAIGN IS ENABLED FOR SYNCING!
    # TODO: Consider status of personemailgruppe (contact) also
    def _get_openerp_data(self):
        peg_record = super(ContactExporter, self)._get_openerp_data()
        assert peg_record.zgruppedetail_id.sync_with_getresponse, (
                "The campaign (zgruppedetail) %s of the contact (personemailgruppe) %s is not enabled to sync with"
                " GetResponse!" % (peg_record.zgruppedetail_id.id, peg_record.id)
        )
        return peg_record

    def delayed_contact_binding_after_export(self, binding_id, contact_email, contact_campaing_id):
        self.binding_id = binding_id
        self.binding_record = self._get_openerp_data()

        contact_ids = self.backend_adapter.search(getresponse_campaign_id=contact_campaing_id, email=contact_email)

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
        
        # TODO: Create a delayed binding job with some retries (1, 2, 4, 8 minutes)
        #       Maybe it would be better to just run some sort of regular contact import?
        #       I really think an import would be better - this could update the sync_data and other stuff also!!!
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
