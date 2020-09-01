# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import json

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ImportMapper, mapping, only_create
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
class CustomFieldImportMapper(ImportMapper):
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
        return {'backend_id': self.backend_record.id}

    @mapping
    def getresponse_id(self, record):
        return {'getresponse_id': record['id']}


# ---------------------------------------------------------------------------------------------------------------------
# IMPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------


# --------------
# BATCH IMPORTER
# --------------
@getresponse
class CustomFieldBatchImporter(BatchImporter):
    _model_name = ['getresponse.gr.custom_field']


@job(default_channel='root.getresponse')
def custom_field_import_batch(session, model_name, backend_id, filters=None, delay=False, **kwargs):
    """ Prepare the batch import for all GetResponse Custom Field Definitions """
    if filters is None:
        filters = {}
    connector_env = get_environment(session, model_name, backend_id)

    # Get the import connector unit
    importer = connector_env.get_connector_unit(CustomFieldBatchImporter)

    # Start the batch import
    importer.batch_run(filters=filters, delay=delay, **kwargs)


# ----------------------
# IMPORT A SINGLE RECORD
# ----------------------
# In this class we could alter the generic GetResponse import sync flow for 'getresponse.frst.zgruppedetail'
# HINT: We could overwrite all the methods from the shared GetResponseImporter here if needed!
@getresponse
class CustomFieldImporter(GetResponseImporter):
    _model_name = ['getresponse.gr.custom_field']

    _base_mapper = CustomFieldImportMapper

    def bind_before_import(self):
        binding = self.binding_record
        # Skipp bind_before_import() because a binding was already found for the getresponse_id.
        if binding:
            return binding

        # The record data read from GetResponse as a dict()
        map_record = self._get_map_record()

        # Odoo update data (vals dict for odoo fields)
        odoo_record_update_data = self._update_data(map_record)

        # The external id from the getresponse record data dict
        getresponse_id = self.getresponse_id

        # The unique custom field definition name
        getresponse_custom_field_name = odoo_record_update_data['name']

        # The backend id
        backend_id = self.backend_record.id

        # EXISTING PREPARED BINDING (binding without external id)
        prepared_binding = self.model.search([('backend_id', '=', backend_id),
                                              ('name', '=', getresponse_custom_field_name)])
        if prepared_binding:
            assert len(prepared_binding) == 1, 'More than one binding found for this custom field definition name!'
            assert not prepared_binding.getresponse_id, 'Prepared binding has a getresponse_id?'
            self.binder.bind(getresponse_id, prepared_binding.id)
            return prepared_binding

        # EXISTING CUSTOM FIELD DEFINITION
        unwrapped_model = self.binder.unwrap_model()
        custom_field = self.env[unwrapped_model].search([('name', '=', getresponse_custom_field_name)])
        if custom_field:
            assert len(custom_field) == 1, "More than one custom field definition with this name found!"
            prepared_binding = self.binder._prepare_binding(custom_field.id)
            self.binder.bind(getresponse_id, prepared_binding.id)
            return prepared_binding

        # Nothing found so we return the original method result
        return super(CustomFieldImporter, self).bind_before_import()
