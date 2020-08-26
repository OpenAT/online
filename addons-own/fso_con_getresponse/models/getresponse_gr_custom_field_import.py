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
# Transform the data from GetResponse campaign objects to odoo records and vice versa
@getresponse
class GrCustomFieldImportMapper(ImportMapper):
    """ Map all the fields of the getresponse-python library object to the odoo record fields.

    ATTENTION: The field names of the  GetResponse API library (getresponse-python) may not match the field names
               found in the getresponse API documentation e.g. Campaign.language_code is 'languageCode' in the api.
               Check getresponse-python > custom_field.py for the mappings
    """
    _model_name = 'getresponse.gr.custom_field'

    def _map_children(self, record, attr, model):
        pass

    # Direct mappings
    # ('source: getresponse-python object field', 'target: odoo record field')
    direct = [('name', 'name'),
              ('type', 'gr_type'),
              ('format', 'gr_format'),
              ('hidden', 'gr_hidden'),
              # ('values', 'gr_values')
              ]

    # ATTENTION: The python lib will already convert values from a json string to a python object!
    @mapping
    def gr_values(self, record):
        if record['values']:
            values_json = json.dumps(record['values'], encoding='utf-8', ensure_ascii=False)
        else:
            values_json = False
        return {'gr_values': values_json}

    @mapping
    def backend_id(self, record):
        # TODO: Get the field name '_openerp_field' from the binder for 'getresponse.gr.tag'
        return {'backend_id': self.backend_record.id}

    @mapping
    def getresponse_id(self, record):
        # TODO: Get the field name '_openerp_field' from the binder for 'getresponse.gr.tag'
        return {'getresponse_id': record['id']}


# ---------------------------------------------------------------------------------------------------------------------
# IMPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------


# --------------
# BATCH IMPORTER
# --------------
@getresponse
class GrCustomFieldBatchImporter(BatchImporter):
    _model_name = ['getresponse.gr.custom_field']


@job(default_channel='root.getresponse')
def gr_custom_field_import_batch(session, model_name, backend_id, filters=None, delay=False, **kwargs):
    """ Prepare the batch import for all GetResponse Custom Field Definitions """
    if filters is None:
        filters = {}
    connector_env = get_environment(session, model_name, backend_id)

    # Get the import connector unit
    importer = connector_env.get_connector_unit(GrCustomFieldBatchImporter)

    # Start the batch import
    importer.batch_run(filters=filters, delay=delay, **kwargs)


# ----------------------
# IMPORT A SINGLE RECORD
# ----------------------
# In this class we could alter the generic GetResponse import sync flow for 'getresponse.frst.zgruppedetail'
# HINT: We could overwrite all the methods from the shared GetResponseImporter here if needed!
@getresponse
class GrCustomFieldImporter(GetResponseImporter):
    _model_name = ['getresponse.gr.custom_field']

    _base_mapper = GrCustomFieldImportMapper

    # BIND RECORDS TO EXISTING GR.CUSTOM_FIELD RECORDS ON IMPORT
    # ----------------------------------------------------------
    #     - Field with the same name exists but no binding -> Create binding before import
    #     - Field with binding exists but binding has no getresponse_id -> Update the binding before import
    def _get_binding(self):
        # HINT: The bind record will be searched/found based on the external_id
        bind_record = super(GrCustomFieldImporter, self)._get_binding()

        map_record = self._map_data()
        mapped_update_data = self._update_data(map_record)

        external_id_field_name = self.binder._external_field
        external_id_in_import_data = mapped_update_data.get(external_id_field_name)

        # ALREADY BOUND TO AN EXTERNAL GETRESPONSE ID: RETURN FOUND BINDING
        if bind_record and getattr(bind_record, external_id_field_name):
            return bind_record

        # SEARCH FOR AN EXISTING CUSTOM FIELD. IF FOUND CREATE OR UPDATE BINDING BEFORE IMPORT
        # HINT: Must be unbound or bound without an external id or super()._get_binding() would have found it
        #       in the first place!
        # INFO: Normally all the mapped import data would be written to the binder model. Because of delegated
        #       inheritance this would create the bind_record and the unwrapped model record at the same time.
        #       But if the custom field exists already we need to create the binding before the import to trigger
        #       an import_update (instead of an create) to bind the existing custom field!
        getresponse_cf_name = mapped_update_data['name']
        original_odoo_model = self.binder.unwrap_model()
        existing_cf = self.env[original_odoo_model].search([('name', '=', getresponse_cf_name)])
        if len(existing_cf) == 1 and external_id_in_import_data:
            # Check if a binding exist already for this backend
            existing_bind_record = existing_cf.getresponse_bind_ids.filtered(
                lambda r: r.backend_id.id == self.backend_record.id)

            # UPDATE AN EXISTING BINDING WITH THE EXTERNAL ID BEFORE IMPORT
            if existing_bind_record:
                assert len(existing_bind_record) == 1, (
                        "Multiple bind records found for the same backend! %s" % str(existing_bind_record))
                assert not getattr(existing_bind_record, external_id_field_name), (
                    "Bind record with correct external id was found?!? bind_record: %s, %s"
                    "" % (existing_bind_record._name, existing_bind_record.id))
                _logger.warning("Binding exists but not bound to an external id! Updating binding before import: "
                                "external_id %s, bind_record_id: %s, bind_record_model: %s"
                                "" % (external_id_in_import_data, bind_record.id, bind_record._name))
                self.binder.bind(external_id_in_import_data, existing_bind_record.id)
                return existing_bind_record

            # CREATE A BINDING FOR AN EXISTING CUSTOM FIELD BEFORE IMPORT
            else:
                binding_vals = {
                    self.binder._backend_field: self.backend_record.id,
                    self.binder._openerp_field: existing_cf.id,
                    self.binder._external_field: external_id_in_import_data,
                }
                _logger.warning("A tag for this name was found! "
                                "Creating binding before import to bind the existing tag! "
                                "binding_vals: %s" % binding_vals)
                # HINT: Add connector_no_export to avoid to trigger the export when we modify the `external_id`
                new_bind_record = bind_record.with_context(connector_no_export=True).create(binding_vals)
                return new_bind_record

        # NO BINDING WAS FOUND
        # HINT: bind_record is an empty recordset
        return bind_record

