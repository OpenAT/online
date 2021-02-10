# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import json
from copy import deepcopy

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ImportMapper, ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job

from .helper_connector import get_environment
from .backend import getresponse
from .unit_import import BatchImporter, GetResponseImporter, import_record
from .unit_export import GetResponseExporter

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
    def backend_id(self, record):
        return {'frst.personemailgruppe.backend_id': self.backend_record.id}

    @mapping
    def getresponse_id(self, record):
        return {'frst.personemailgruppe.getresponse_id': record['id']}

    @mapping
    def zgruppedetail_id(self, getresponse_record):
        # HINT: The Campaign must already exists because we will only import contacts for enabled campaigns
        campaign_binder = self.binder_for('getresponse.frst.zgruppedetail')

        # WARNING: campaign in the getresponse_record dict is still a campaign object and not a dict *grrr*
        campaign_object = getresponse_record['campaign']
        external_campaign_id = campaign_object.id

        zgruppedetail = campaign_binder.to_openerp(external_campaign_id, unwrap=True)
        assert zgruppedetail, "Group (zgruppedetail) not found for external id %s" % external_campaign_id
        return {'frst.personemailgruppe.zgruppedetail_id': zgruppedetail.id}

    @mapping
    def name(self, getresponse_record):
        # ATTENTION: Check finalize() for the handling of name missing or lastname in custom fields!
        return {'res.partner.name': getresponse_record['name']}

    @mapping
    def email(self, getresponse_record):
        return {'frst.personemail.email': getresponse_record['email']}

    @mapping
    def getresponse_tag_ids(self, getresponse_record):
        # ATTENTION: The import would be have been skipped already if the odoo data changed since the last sync and
        #            would have forced an export to GetResponse instead! Therefore we do not need to merge or compare
        #            the odoo tags with the getresponse tags like we do at the contact export mapper

        tags = getresponse_record.get('tags', [])

        # Current GetResponse Tags data
        tags_binder = self.binder_for('getresponse.gr.tag')
        getresponse_tag_ids = []
        for gr_tag in tags:
            # WARNING: The tags in the getresponse_record dict are no objects but the raw data from getresponse
            #          Therefore we have to use the GetResponse api key tagId instead of just id
            tag_external_id = gr_tag['tagId']
            tag = tags_binder.to_openerp(tag_external_id, unwrap=True)

            # Import the tag definition if it does not exist jet in odoo
            if not tag:
                _logger.info("Tag definition '%s' missing in odoo! Trying to import the tag definition!"
                             "" % tag_external_id)
                import_record(self.session, 'getresponse.gr.tag', self.backend_record.id, tag_external_id,
                              skip_export_related_bindings=True, skip_import_related_bindings=True)
                tag = tags_binder.to_openerp(tag_external_id, unwrap=True)

            assert tag, "Odoo Tag Definition for external id %s missing!" % tag_external_id
            getresponse_tag_ids.append(tag.id)

        # (6, _, ids) replaces all existing records in the set by the ids list
        # result = [(6, 0, getresponse_tag_ids)] if getresponse_tag_ids else False
        # ATTENTION: 'False' will !!! NOT !!! empty a many2many field!
        result = [(6, 0, getresponse_tag_ids)]
        return {'res.partner.getresponse_tag_ids': result}

    @mapping
    def custom_fields(self, getresponse_record):
        # ATTENTION: The import would be have been skipped already if the odoo data changed since the last sync and
        #            would have forced an export to GetResponse instead! Therefore we do not need to merge or compare
        #            the odoo custom field data with getresponse like we do at the contact export mapper
        #
        # ATTENTION: GetResponse fields with a value list can NOT have an empty value but must use one of the
        #            values of the custom field definition!
        #
        # ATTENTION: I !GUESS! that if no value is given to a custom field the field will be missing completely in the
        #            custom_field_values of the contact. Therefore we check if fields are missing since the last sync
        #            and set the odoo value to False if the field definitions still exits in odoo and are still mapped!
        getresponse_custom_field_data = getresponse_record.get('custom_field_values', {})

        # Get the last sync field data if any
        # contact_binder = self.binder_for('getresponse.frst.personemailgruppe')
        # binding = contact_binder.to_openerp(getresponse_record['id'])
        # last_sync_field_data = {}
        # if binding.compare_data:
        #     last_sync_cmp_data = json.loads(binding.compare_data, encoding='utf8')
        #     if 'customFieldValues' in last_sync_cmp_data:
        #         last_custom_field_values = last_sync_cmp_data['customFieldValues']
        #         last_sync_field_data = {f['customFieldId']: f['value'] for f in last_custom_field_values}

        # CONVERT THE CUSTOM FIELD VALUES FROM GETRESPONSE TO ODOO FIELD NAMES AND VALUES
        # -------------------------------------------------------------------------------
        cf_binder = self.binder_for('getresponse.gr.custom_field')
        result = {}
        for gr_cf in getresponse_custom_field_data:

            # Get the custom field definition record
            custom_field_ext_id = gr_cf['customFieldId']
            odoo_cf = cf_binder.to_openerp(custom_field_ext_id, unwrap=True)

            # Import the custom field definition if it does not exist jet in odoo
            if not odoo_cf:
                _logger.info("Custom field definition '%s' missing in odoo! Trying to import the definition!"
                             "" % custom_field_ext_id)
                import_record(self.session, 'getresponse.gr.custom_field', self.backend_record.id, custom_field_ext_id,
                              skip_export_related_bindings=True, skip_import_related_bindings=True)
                odoo_cf = cf_binder.to_openerp(custom_field_ext_id, unwrap=True)

            assert odoo_cf, "Odoo Custom Field Definition for external id %s missing!" % custom_field_ext_id

            # Only get values for mapped custom fields
            if not odoo_cf.field_id:
                continue

            # Check the model of the custom field
            assert odoo_cf.field_model_name in ('res.partner', 'frst.personemail', 'frst.personemailgruppe'), (
                "Unsupported custom field model %s" % odoo_cf.field_model_name)

            # Convert the GetResponse value to an odoo field value
            values = gr_cf['values']
            assert len(values) == 1, 'Multi Values are not supported for a mapped custom field! %s' % values
            odoo_value = odoo_cf.get_odoo_value(values[0])

            # Prepend the model name to the value key
            # HINT: Check finalize()  and create() and update() for the deconstruction of the cf values
            odoo_model_and_field_name = odoo_cf.field_model_name + '.' + odoo_cf.field_id.name

            # Append the custom field data
            result[odoo_model_and_field_name] = odoo_value

        # SET FIELD VALUE TO 'False' FOR FIELDS THAT WHERE UNAMBIGUOUSLY REMOVED IN GETRESPONSE SINCE THE LAST SYNC
        # ---------------------------------------------------------------------------------------------------------
        current_gr_contact_custom_field_ids = [grcf['customFieldId'] for grcf in getresponse_custom_field_data]
        contact_binder = self.binder_for('getresponse.frst.personemailgruppe')
        contact_binding = contact_binder.to_openerp(getresponse_record['id'])
        if contact_binding.compare_data:
            # Get the compare data (getresponse payload) of the last sync
            last_sync_cmp_data = json.loads(contact_binding.compare_data, encoding='utf8')
            if 'customFieldValues' in last_sync_cmp_data:
                # Get the external custom field ids of the last sync
                last_sync_contact_custom_fields = last_sync_cmp_data['customFieldValues']
                last_sync_custom_field_ids = [lscf['customFieldId'] for lscf in last_sync_contact_custom_fields]
                for last_sync_fid in last_sync_custom_field_ids:
                    if last_sync_fid not in current_gr_contact_custom_field_ids:
                        odoo_cf = cf_binder.to_openerp(last_sync_fid, unwrap=True)
                        # Do NOT clear odoo-record-field-value for removed, unmapped or custom fields of the wrong model
                        if not odoo_cf or not odoo_cf.field_id or odoo_cf.field_model_name not in (
                                'res.partner', 'frst.personemail', 'frst.personemailgruppe'):
                            continue
                        # CLEAR THE ODOO FIELD VALUE BECAUSE THE CUSTOM FIELD OF THE CONTACT WAS REMOVED IN GETRESPONSE
                        odoo_model_and_field_name = odoo_cf.field_model_name + '.' + odoo_cf.field_id.name
                        result[odoo_model_and_field_name] = False
        
        # Return the result
        return result

    def finalize(self, map_record, values):
        """ Called at the end of the mapping.

        Can be used to modify the values before returning them, as the
        ``on_change``.

        :param map_record: source map_record
        :type map_record: :py:class:`MapRecord`
        :param values: mapped values
        :returns: mapped values
        :rtype: dict
        """

        result = {'res.partner': {},
                  'frst.personemail': {},
                  'frst.personemailgruppe': {},
                  }
        for key, value in values.iteritems():
            split = key.rsplit('.', 1)
            assert len(split) == 2, "Unexpected key found in contact data: %s" % split

            odoo_model_name = split[0]
            assert odoo_model_name in result.keys(), (
                    'Unknown model name in contact data: %s (%s, %s)' % (odoo_model_name, key, value))

            odoo_field_name = split[1]

            result[odoo_model_name][odoo_field_name] = value

        # ASSERTIONS
        # ----------
        assert result['frst.personemailgruppe']['zgruppedetail_id'], _(
            "zgruppedetail_id missing in contact data! %s" % values)
        assert result['frst.personemail']['email'], "'email' missing in personemail data! %s" % values

        # res.partner 'no name' handling
        # ------------------------------
        if not any(result['res.partner'].get(f, '') for f in ('name', 'firstname', 'lastname')):
            result['res.partner']['lastname'] = result['frst.personemail']['email']

        # res.partner firstname and lastname handling
        # -------------------------------------------
        if any(result['res.partner'].get(f, '') for f in ('firstname', 'lastname')):
            result['res.partner'].pop('name', None)
        else:
            if result['res.partner'].get('name'):
                result['res.partner'].pop('firstname', None)
                result['res.partner'].pop('lastname', None)

        # Return the final odoo data
        return result


# ---------------------------------------------------------------------------------------------------------------------
# IMPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------

# --------------
# BATCH IMPORTER
# --------------
@getresponse
class ContactBatchImporter(BatchImporter):
    _model_name = ['getresponse.frst.personemailgruppe']

    def _batch_run_search(self, per_page=None, page=None, params=None, getresponse_campaign_ids=None, name=None,
                          email=None, custom_fields=None, **kwargs):

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

        # Do a paged search for the records
        all_records = []
        paged_records = True
        current_page = deepcopy(page) if page else 1
        while paged_records and current_page:
            paged_records = self.backend_adapter.search(getresponse_campaign_ids=getresponse_campaign_ids,
                                                        per_page=per_page,
                                                        page=current_page,
                                                        params=params)
            all_records.extend(paged_records)

            # The page is controlled from outside (only the results from the requested page will be returned)
            if page:
                current_page = None
            # The page is controlled here and will be incremented until no more records are found
            else:
                current_page += 1

        return all_records


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
            msg = _('Contact import SKIPPED because campaign (zgruppedetail) is not imported yet or not enabled for'
                    'syncing with GetResponse! %s' % self.getresponse_id)
            _logger.warning(msg)
            return msg
        else:
            return False

    def _create(self, data):
        model_no_export = self.model.with_context(connector_no_export=True)

        # Get the data
        peg_binding_data = data['frst.personemailgruppe']
        personemail_data = data['frst.personemail']
        partner_data = data['res.partner']

        # CREATE THE PARTNER
        # HINT: We add the email to the res.partner create data to automatically create the frst.personemail
        partner_data['email'] = personemail_data['email']
        partner = model_no_export.env['res.partner'].create(partner_data)

        # Check the auto-generated frst.personemail
        personemail = partner.main_personemail_id
        assert personemail.email == partner.email == partner_data['email'], _(
            "The emails do not match! (%s, %s, %s)" % (personemail.email, partner.email, partner_data['email']))

        # UPDATE THE PERSONEMAIL IF NEEDED
        # ATTENTION: Since the context of the created partner is with connector_no_export=True it should not be needed
        #            to set the context again here.
        if len(personemail_data) > 1:
            personemail.write(personemail_data)

        # CREATE THE NEW BINDING AND THEREFORE THE UNWRAPPED ODOO RECORD
        # HINT: We append the new personemail to the peg binding data
        peg_binding_data['frst_personemail_id'] = personemail.id
        peg_binding = model_no_export.create(peg_binding_data)

        return peg_binding

    def _update(self, binding, data, dry_run=False):
        # binding_no_export = binding.with_context(connector_no_export={binding._name: [binding.id]})
        binding_no_export = binding.with_context(connector_no_export=True)

        def _remove_unchanged(update_data, record):
            result = {}
            for f_name, update_value in update_data.iteritems():
                if f_name not in record._fields:
                    continue
                f_type = record._fields[f_name].type
                if f_type in ('many2one', 'one2many', 'many2many'):
                    record_value = getattr(record, f_name).ids
                    if update_value and isinstance(update_value, basestring):
                        update_value = int(update_value)
                    compare_value = update_value if isinstance(update_value, list) else \
                        [update_value] if update_value else []
                    if len(compare_value) == 1 and isinstance(compare_value[0], tuple) and compare_value[0][0] == 6:
                        compare_value = compare_value[0][2]
                    record_value = set(record_value)
                    compare_value = set(compare_value)
                else:
                    record_value = getattr(record, f_name)
                    compare_value = update_value

                # Compare the sets of ids for related fields or regular field data
                if record_value != compare_value:
                    _logger.info("Odoo record data '%s' does not match getresponse mapper data '%s' for '%s.%s'"
                                 "" % (record_value, compare_value, record._name, f_name))
                    result[f_name] = update_value

            return result

        # personemailgruppe
        peg_binding_mdata = data['frst.personemailgruppe']
        peg_binding = binding_no_export
        # ATTENTION: Remove simple char fields from the update if the data did not change. This will not work for
        #            any relation field.
        peg_binding_data = _remove_unchanged(peg_binding_mdata, peg_binding)
        if peg_binding_data:
            _logger.info("peg_binding_mapper_data: %s" % peg_binding_mdata)
            _logger.info("peg_binding_changed_data: %s" % peg_binding_data)

        # personemail
        personemail_mdata = data['frst.personemail']
        personemail = peg_binding.frst_personemail_id
        # ATTENTION: Remove simple char fields from the update if the data did not change. This will not work for
        #            any relation field. The reason to remove unchanged data is to avoid e.g.: main email changes and
        #            alike!
        personemail_data = _remove_unchanged(personemail_mdata, personemail)
        if personemail_data:
            _logger.info("personemail_mapper_data: %s," % personemail_mdata)
            _logger.info("personemail_changed_data: %s" % personemail_data)

        # partner data
        partner_mdata = data['res.partner']
        partner = personemail.partner_id
        # ATTENTION: Remove simple char fields from the update if the data did not change. This will not work for
        #            any relation field. The reason to remove unchanged data is to avoid e.g.: bpk changes and
        #            alike!
        partner_data = _remove_unchanged(partner_mdata, partner)
        if partner_data:
            _logger.info("partner_mapper_data: %s" % partner_mdata)
            _logger.info("partner_changed_data: %s" % partner_data)

        assert personemail_mdata['email'] == personemail.email, "The email can not be changed! %s, %s" % (data, binding)

        # ----------------------------------------------------
        # SKIPP THE ODOO RECORD UPDATE BECAUSE NO DATA CHANGED
        # ----------------------------------------------------
        if not partner_data and not personemail_data and not peg_binding_data:
            _logger.info("SKIPP ContactImporter._update() for binding '%s' '%s' since no relevant data changed "
                         "in GetResponse!" % (binding.id, binding._name))
            return True

        # ---------------------------------------------
        # UPDATE THE ODOO RECORDS WITH THE CHANGED DATA
        # ---------------------------------------------
        # UPDATE THE PERSON
        # ATTENTION: The partner should have already the context connector_no_export={binding._name: [binding.id]}
        if partner_data and not dry_run:
            assert partner.write(partner_data), "Could not update partner! %s" % partner

        # UPDATE THE PERSONEMAIL
        # ATTENTION: The personemail should have already the context connector_no_export={binding._name: [binding.id]}
        if personemail_data and not dry_run:
            assert personemail.write(personemail_data), "Could not update personemail! %s" % personemail

        # UPDATE THE BINDING RECORD (and therefore the regular odoo record (delegation inheritance) also
        if peg_binding_data and not dry_run:
            result = binding_no_export.write(peg_binding_data)
        else:
            result = True

        return result

    def _import_related_bindings(self, *args, **kwargs):
        contact_binding = self.binding_record
        partner = contact_binding.frst_personemail_id.partner_id
        all_contact_bindings = partner.mapped('frst_personemail_ids.personemailgruppe_ids.getresponse_bind_ids')
        related_contact_bindings = all_contact_bindings - contact_binding
        for related_binding in related_contact_bindings:
            # FORCE EXPORT THE BINDING
            exporter = self.unit_for(GetResponseExporter)
            _logger.info("IMPORT: Export related contact binding '%s', '%s' to '%s' AFTER IMPORT OF '%s', '%s'!"
                         "" % (related_binding._name, related_binding.id, related_binding.getresponse_id,
                               contact_binding._name, contact_binding.id))
            exporter.run(contact_binding.id, skip_import_related_bindings=True)

    # Do bind before import if there is a prepared binding waiting for this email for the rare event that an
    # import is triggered before the delayed binding job gets executed
    def bind_before_import(self):
        binding = self.binding_record
        # Skipp bind_before_import() because a binding was already found for the external getresponse_id.
        if binding:
            return binding

        # The external id from the getresponse record data dict
        getresponse_id = self.getresponse_id

        # The getresponse record object
        getresponse_record = self.getresponse_record

        # The backend id
        backend_id = self.backend_record.id

        # The group (zgruppedetail) this contact (personemailgruppe) belongs to
        campaign_binder = self.binder_for('getresponse.frst.zgruppedetail')
        external_campaign_id = getresponse_record['campaign'].id
        zgruppedetail = campaign_binder.to_openerp(external_campaign_id, unwrap=True)
        zgruppedetail_id = zgruppedetail.id if zgruppedetail else None
        if not zgruppedetail_id:
            return super(ContactImporter, self).bind_before_import()

        # The unique email of the contact (personemailgruppe)
        email = getresponse_record['email']

        # EXISTING PREPARED BINDING (binding without external id)
        prepared_binding = self.model.search([('backend_id', '=', backend_id),
                                              ('zgruppedetail_id', '=', zgruppedetail_id),
                                              ('frst_personemail_id.email', '=', email)])
        if prepared_binding:
            assert len(prepared_binding) == 1, 'More than one binding found for this contact name!'
            assert not prepared_binding.getresponse_id, 'Prepared binding has a getresponse_id?'
            # Update the prepared binding before the import
            prepared_binding.with_context(connector_no_export=True).write({'getresponse_id': getresponse_id})
            # contact_importer.binder.bind(getresponse_contact_id, binding_id,
            #                              sync_data='DELAYED CONTACT BINDING',
            #                              compare_data=False)
            _logger.info(
                "BIND BEFORE IMPORT: Prepared Contact Binding '%s', '%s', was bound to '%s' before import!"
                "" % (prepared_binding._name, prepared_binding.id, getresponse_id))
            return prepared_binding

        # -------------------------------------------------------------------------------------------------------------
        # DISABLED: Because we do not want to change existing person data just because someone guessed the right email
        #           Instead we just create a new partner and let the 'dublettenpruefung' of FRST decide to merge the
        #           contacts or not!
        # -------------------------------------------------------------------------------------------------------------
        # EXISTING CONTACT (PERSONEMAILGRUPPE) WITHOUT BINDING
        # unwrapped_model = self.binder.unwrap_model()
        # peg = self.env[unwrapped_model].search([('zgruppedetail_id', '=', zgruppedetail_id),
        #                                         ('frst_personemail_id.email', '=', email)])
        # if peg:
        #     assert len(peg) == 1, ("More than one contact (personemailgruppe %s) with this email %s found for this "
        #                                "campaing (zgruppedetail %s)!" % (peg.ids, email, zgruppedetail_id))
        #     prepared_binding = self.binder._prepare_binding(peg.id)
        #     self.binder.bind(getresponse_id, prepared_binding.id)
        #     return prepared_binding

        # Nothing found so we return the original method result
        return super(ContactImporter, self).bind_before_import()
