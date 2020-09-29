# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
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
class TagImportMapper(ImportMapper):
    """ Map all the fields of the the getresponse-python library object to the odoo record fields.

    ATTENTION: The field names of the  GetResponse API library (getresponse-python) may not match the field names
               found in the getresponse API documentation e.g. Campaign.language_code is 'languageCode' in the api.
               Check _create() from getresponse-python > tag.py for the mappings
    """
    _model_name = 'getresponse.gr.tag'

    def _map_children(self, record, attr, model):
        pass

    # Direct mappings
    # ('source: getresponse-python object field', 'target: odoo record field')
    direct = [('name', 'name')]

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
class TagBatchImporter(BatchImporter):
    _model_name = ['getresponse.gr.tag']


@job(default_channel='root.getresponse')
def tag_import_batch(session, model_name, backend_id, filters=None, delay=False, **kwargs):
    """ Prepare the batch import for all GetResponse Tag Definitions found in GetResponse """
    if filters is None:
        filters = {}
    connector_env = get_environment(session, model_name, backend_id)

    # Get the import connector unit
    importer = connector_env.get_connector_unit(TagBatchImporter)

    # Start the batch import
    importer.batch_run(filters=filters, delay=delay, **kwargs)


# ----------------------
# IMPORT A SINGLE RECORD
# ----------------------
@getresponse
class TagImporter(GetResponseImporter):
    _model_name = ['getresponse.gr.tag']

    _base_mapper = TagImportMapper

    # BIND RECORDS TO EXISTING GR.TAG RECORDS OR PREPARED BINDINGS BEFORE IMPORT
    # --------------------------------------------------------------------------
    #     - Tag with the same name exists but no binding -> Create binding before import
    #     - Tag with binding exists but binding has no getresponse_id -> Update the binding before import
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

        # The unique tag name
        getresponse_tag_name = odoo_record_update_data['name']

        # The backend id
        backend_id = self.backend_record.id

        # EXISTING PREPARED BINDING (binding without external id)
        prepared_binding = self.model.search([('backend_id', '=', backend_id),
                                              ('name', '=', getresponse_tag_name)])
        if prepared_binding:
            assert len(prepared_binding) == 1, 'More than one binding found for this tag name!'
            assert not prepared_binding.getresponse_id, 'Prepared binding has a getresponse_id?'
            self.binder.bind(getresponse_id, prepared_binding.id)
            return prepared_binding

        # EXISTING TAG
        unwrapped_model = self.binder.unwrap_model()
        tag = self.env[unwrapped_model].search([('name', '=', getresponse_tag_name)])
        if tag:
            assert len(tag) == 1, "More than one tag with this name found!"
            prepared_binding = self.binder._prepare_binding(tag.id)
            self.binder.bind(getresponse_id, prepared_binding.id)
            return prepared_binding

        return super(TagImporter, self).bind_before_import()
