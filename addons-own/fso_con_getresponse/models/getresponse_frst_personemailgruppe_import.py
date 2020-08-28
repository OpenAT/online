# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import json

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ImportMapper, ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job

from .helper_connector import get_environment
from .backend import getresponse
from .unit_import import BatchImporter, GetResponseImporter

import logging
_logger = logging.getLogger(__name__)


# -----------------------
# CONNECTOR IMPORT MAPPER
# -----------------------
# Transform the data from GetResponse contact objects to odoo records and vice versa
@getresponse
class ContactImportMapper(ImportMapper):
    """ Map all the fields of the the GetResponse API library contact object to the odoo record fields.
    You can find all all available fields here: ..../getresponse-python/getresponse/contact.py

    ATTENTION: The field names of the  GetResponse API library (getresponse-python) may not match the field names
               found in the getresponse API documentation e.g. language_code is 'languageCode' in the api.
               The final transformation to the correct API names is done by the getresponse-python lib. Check
               _create() from getresponse-python > contact.py to see the final transformations
    """
    _model_name = 'getresponse.frst.personemailgruppe'

    # TODO: Check if this method may be the correct one for PersonEmail and Partner for PersonEmailGruppe"
    def _map_children(self, record, attr, model):
        pass

    # ATTENTION: We need a flat dict of data because nested dicts will not be merged by .update() - Therefore
    #            we create a structure like this {'partner.name': 'bob', 'partner.email': 'bob@gmail.com'}
    #            This one dimensional dict will then be separated again in create and write of the import .run()

    # ATTENTION: Do not forget that the getresponse record is a dict - and not the real object returned from the lib!
    #            Therefore we must use getresponse_record['name'] instead of getresponse_record.name

    @mapping
    def zgruppedetail_id(self, getresponse_record):
        # HINT: The Campaign must already exists because we will only import contacts for enabled campaigns
        campaign_binder = self.binder_for('getresponse.frst.zgruppedetail')

        # WARNING: campaign in the getresponse_record dict is still a campaign object and not a dict *grrr*
        campaign_object = getresponse_record['campaign']
        external_campaign_id = campaign_object.id

        zgruppedetail = campaign_binder.to_openerp(external_campaign_id, unwrap=True)
        assert zgruppedetail, "Group (zgruppedetail) not found for external id %s" % external_campaign_id
        return {'zgruppedetail_id': zgruppedetail.id}

    @mapping
    def name(self, getresponse_record):
        return {'res.partner.name': getresponse_record['name']}

    @mapping
    def email(self, getresponse_record):
        return {'res.partner.email': getresponse_record['email']}

    @mapping
    def getresponse_tag_ids(self, getresponse_record):
        tags = getresponse_record.get('tags', [])

        tags_binder = self.binder_for('getresponse.gr.tag')
        getresponse_tag_ids = []
        for gr_tag in tags:
            # WARNING: The tags in the getresponse_record dict are no objects but the raw data from getresponse
            #          Therefore we have to use the GetResponse api key tagId instead of just id
            tag = tags_binder.to_openerp(gr_tag['tagId'], unwrap=True)
            assert tag, "Odoo Tag Definition for external id %s missing!" % gr_tag['tagId']
            getresponse_tag_ids.append(tag.id)

        # Search for an existing bound record (by external id)
        contact_binder = self.binder_for('getresponse.frst.personemailgruppe')
        contact_binding = contact_binder.to_openerp(getresponse_record['id'])

        # If no binding was found this must be a contact 'create' so we just return the data
        if not contact_binding:
            return {'partner.getresponse_tag_ids': getresponse_tag_ids}

        # TODO: FOR UPDATES COMPARE DATA FOR THE FINAL TAG LIST
        # TODO Get the last sync data tags
        last_sync_data = json.loads(contact_binding.sync_data, encoding='utf8') if contact_binding.sync_data else {}
        last_sync_tags = last_sync_data.get('tags')
        # TODO: Get the current odoo res.partner tags
        # TODO: Create and return final tag list

    @mapping
    def custom_fields(self, getresponse_record):
        custom_field_values = getresponse_record.get('custom_field_values', {})

        cf_binder = self.binder_for('getresponse.gr.custom_field')
        result = {}
        for gr_cf in custom_field_values:

            # Get the custom field definition record
            odoo_cf = cf_binder.to_openerp(gr_cf['customFieldId'], unwrap=True)
            assert odoo_cf, "Odoo Custom Field Definition for external id %s missing!" % gr_cf['customFieldId']

            # Only get values for mapped custom fields
            if not odoo_cf.field_id:
                continue

            # Check the model of the custom field
            assert odoo_cf.field_model_name in ('res.partner', 'frst.personemail', 'frst.personemailgruppe'), (
                "Unsupported custom field model %s" % odoo_cf.field_model_name)

            # Get the odoo value
            values = gr_cf['values']
            assert len(values) == 1, 'Multi Values are not supported for a mapped custom field! %s' % values
            raw_value = values[0]
            assert raw_value, 'Empty values for custom fields should not be supported by GetResponse?!? %s' % raw_value
            odoo_value = odoo_cf.get_odoo_value(raw_value)

            # Prepend the model name to the value key if the model is not 'frst.personemailgruppe'
            # HINT: Check create and update of the importer to see the deconstruction of the values
            prefix = odoo_cf.field_model_name if odoo_cf.field_model_name != 'frst.personemailgruppe' else ''
            key = prefix + '.' + odoo_cf.field_id.name

            # Append the custom field data
            result[key] = odoo_value

        # Search for an existing bound record (by external id)
        contact_binder = self.binder_for('getresponse.frst.personemailgruppe')
        contact_binding = contact_binder.to_openerp(getresponse_record['id'])

        # If no binding was found this must be a contact 'create' so we just return the data
        if not contact_binding:
            return result

        # TODO: FOR UPDATES COMPARE DATA FOR FINAL CUSTOM FIELD VALUES
        # WARNING: ONLY REMOVE CUSTOM FIELD VALUES IF THERE IS LAST SYNC DATA AND THERE WAS A VALUE ON THE LAST SYNC
        # GetResponse Custom Fields
        mapped_custom_fields = self.session.env['gr.custom_field'].sudo().search([('field_id', "!=", False)])


# ---------------------------------------------------------------------------------------------------------------------
# IMPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------

# --------------
# BATCH IMPORTER
# --------------
@getresponse
class ContactBatchImporter(BatchImporter):
    _model_name = ['getresponse.frst.personemailgruppe']

    def _batch_run_search(self, getresponse_campaign_ids=None, name=None, email=None, custom_fields=None, **kwargs):

        # Search only for contacts for sync enabled bound campaigns
        getresponse_campaign_ids = [] if not getresponse_campaign_ids else getresponse_campaign_ids
        if not getresponse_campaign_ids:
            campaign_binder = self.binder_for('getresponse.frst.zgruppedetail')
            enabled_campaign_bindings = campaign_binder.get_bindings()
            getresponse_campaign_ids = []
            for cmp_binding in enabled_campaign_bindings:
                getresponse_cmp_id = campaign_binder.to_backend(cmp_binding.id)
                if getresponse_cmp_id:
                    getresponse_campaign_ids.append(getresponse_cmp_id)
            assert getresponse_campaign_ids, "No bound and sync enabled Campaigns found for the Contact batch import!"

        return self.backend_adapter.search(getresponse_campaign_ids=getresponse_campaign_ids)


@job(default_channel='root.getresponse')
def contact_import_batch(session, model_name, backend_id, filters=None, delay=False, **kwargs):
    """ Prepare the batch import of all GetResponse contacts """
    if filters is None:
        filters = {}
    connector_env = get_environment(session, model_name, backend_id)

    # Get the import connector unit
    importer = connector_env.get_connector_unit(ContactBatchImporter)

    # Start the batch import
    importer.batch_run(filters=filters, delay=delay, **kwargs)


# ----------------------
# IMPORT A SINGLE RECORD
# ----------------------
# In this class we could alter the generic GetResponse import sync flow for 'getresponse.frst.personemailgruppe'
# HINT: We could overwrite all the methods from the shared GetResponseImporter here if needed!
@getresponse
class ContactImporter(GetResponseImporter):
    _model_name = ['getresponse.frst.personemailgruppe']

    _base_mapper = ContactImportMapper

    # HINT: We need to do this here and not in skip_by_binding because skipp by binding will only work for updates
    #       so where a binding record for the contact exists already but we want to suppress also creates of contacts
    #       if the campaign is not imported (or bound) yet or if the campaign has the wrong settings.
    #       In theory this should NEVER happen because we import (search) only for contacts for existing and enabled
    #       campaigns (zgruppedetail) in the batch import.
    def skip_by_getresponse_data(self):
        # Skipp if the campaign (zgruppedetail) is not imported yet or not enabled for syncing
        getresponse_record = self.getresponse_record
        campaign_binder = self.binder_for('getresponse.frst.zgruppedetail')
        # WARNING: campaign in the getresponse_record dict is still a campaign object and not a dict *grrr*
        campaign_object = getresponse_record['campaign']
        external_campaign_id = campaign_object.id
        zgruppedetail = campaign_binder.to_openerp(external_campaign_id, unwrap=True)
        if not zgruppedetail or not zgruppedetail.sync_with_getresponse:
            return _('Contact import SKIPPED because campaign (zgruppedetail) is not imported yet or not enabled for'
                     'syncing with GetResponse! %s' % self.getresponse_id)
        else:
            return False

    def _create(self, data):
        # TODO: We need to create partner first the personemail and then the personemailgruppe
        # Deconstruct the data dict and create the three records


    def _update(self, binding, data):
        # TODO: We need to update the partner the personemail and the personemailgruppe
        # Deconstruct the data and update the three records if needed
        # (Make sure the E-Mail did not change)


    # ----------------------------------------------------------------------------------------------------------------
    # DISABLED: Because we do not want to change existing person data just because someone guessed the right email
    #           Instead we just create a new partner and let the 'dublettenpruefung' of FRST decide to merge the
    #           contacts or not!
    # ----------------------------------------------------------------------------------------------------------------
    # def bind_before_import(self):
    #     binding = self.binding_record
    #     # Skipp bind_before_import() because a binding was already found for the getresponse_id.
    #     if binding:
    #         return binding
    #
    #     # The external id from the getresponse record data dict
    #     getresponse_id = self.getresponse_id
    #
    #     # The getresponse record object
    #     getresponse_record = self.getresponse_record
    #
    #     # The backend id
    #     backend_id = self.backend_record.id
    #
    #     # The group (zgruppedetail) this contact (personemailgruppe) belongs to
    #     getresponse_record = self.getresponse_record
    #     campaign_binder = self.binder_for('getresponse.frst.zgruppedetail')
    #     external_campaign_id = getresponse_record.campaign.id
    #     zgruppedetail = campaign_binder.to_openerp(external_campaign_id, unwrap=True)
    #     zgruppedetail_id = zgruppedetail.id if zgruppedetail else None
    #     if not zgruppedetail_id:
    #         return super(ContactImporter, self).bind_before_import()
    #
    #     # The unique email of the contact (personemailgruppe)
    #     email = getresponse_record.email
    #
    #     # EXISTING PREPARED BINDING (binding without external id)
    #     prepared_binding = self.model.search([('backend_id', '=', backend_id),
    #                                           ('zgruppedetail_id', '=', zgruppedetail_id),
    #                                           ('frst_personemail_id.email', '=', email)])
    #     if prepared_binding:
    #         assert len(prepared_binding) == 1, 'More than one binding found for this contact name!'
    #         assert not prepared_binding.getresponse_id, 'Prepared binding has a getresponse_id?'
    #         self.binder.bind(getresponse_id, prepared_binding.id)
    #         return prepared_binding
    #
    #     # EXISTING CONTACT (PERSONEMAILGRUPPE) WITHOUT BINDING
    #     unwrapped_model = self.binder.unwrap_model()
    #     peg = self.env[unwrapped_model].search([('zgruppedetail_id', '=', zgruppedetail_id),
    #                                             ('frst_personemail_id.email', '=', email)])
    #     if peg:
    #         assert len(peg) == 1, ("More than one contact (personemailgruppe %s) with this email %s found for this "
    #                                    "campaing (zgruppedetail %s)!" % (peg.ids, email, zgruppedetail_id))
    #         prepared_binding = self.binder._prepare_binding(peg.id)
    #         self.binder.bind(getresponse_id, prepared_binding.id)
    #         return prepared_binding
    #
    #     # Nothing found so we return the original method result
    #     return super(ContactImporter, self).bind_before_import()
