# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# -----------------------------------------------------------------------------
# This import will either
#     - update the custom field data or
#     - try to delete custom fields in GetResponse that do no longer exist in FSON
# -----------------------------------------------------------------------------
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
    """ Map all the fields of the the GetResponse API library campaign object to the odoo record fields.
    You can find all all available fields here: ..../getresponse-python/getresponse/campaign.py

    ATTENTION: The field names of the  GetResponse API library (getresponse-python) may not match the field names
               found in the getresponse API documentation e.g. Campaign.language_code is 'languageCode' in the api.
               The final transformation to the correct API names is done by the getresponse-python lib. Check
               _create() from getresponse-python > campaign.py to see the final transformations
    """
    _model_name = 'getresponse.gr.custom_field'

    def _map_children(self, record, attr, model):
        pass

    # TODO: map fields


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
    _model_name = ['getresponse.frst.zgruppedetail']

    _base_mapper = GrCustomFieldImportMapper

    # TODO: We can either bind custom fields that do no longer exist in fson or we can skipp them or even try to
    #       delete them in GetResponse ?!?
    def _get_binding(self):
        bind_record = super(GrCustomFieldImporter, self)._get_binding()

        # Search for an existing Group
        # TODO: This is currently the code for campaigns and must be reworked for custom fields
        if not bind_record:
            original_odoo_model = self.binder.unwrap_model()
            map_record_update_data = self._update_data(self._map_data())
            existing_group = self.env[original_odoo_model].search(
                [('gr_name', '=', map_record_update_data['gr_name'])]
            )
            # Create a binding record before the import - so it will trigger an 'update' and not an 'create'
            if len(existing_group) == 1:
                binding_vals = {
                    self.binder._backend_field: self.backend_record.id,
                    self.binder._openerp_field: existing_group.id
                }
                bind_record = self.env[self.model._name].create(binding_vals)
                _logger.info("Created binding for unbound 'GetResponse sync enabled frst.zgruppedetail' before "
                             " import! (binding: %s %s, vals: %s)" % (bind_record._name, bind_record.id, binding_vals))

        return bind_record

