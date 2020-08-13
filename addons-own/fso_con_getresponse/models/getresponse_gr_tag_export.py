# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging
import json

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
class GrTagExportMapper(ExportMapper):
    """ Map all the fields of the odoo record to the GetResponse API field names.

    ATTENTION: !!! FOR THE EXPORT WE MUST USE THE FIELD NAMES OF THE GET RESPONSE API !!!

               When we import data the client lib will return a campaign object. The data of campaign is stored
               in the objects attributes. The pitfall is that the object attributes will follow python conventions so
               the GetResponse 'languageCode' is the attribute campaign.language_code if we read objects from GR.

               BUT for the export to GetResponse (update or write) we need the prepare the "raw data" for the
               request!
    """
    _model_name = 'getresponse.gr.tag'

    def _map_children(self, record, attr, model):
        pass

    # ATTENTION: !!! FOR THE EXPORT WE MUST USE THE RAW FIELD NAMES OF THE GET RESPONSE API !!!

    # Direct mappings
    # ('source: odoo field', 'target: GetResponse api target')
    direct = [('name', 'name')]


# ---------------------------------------------------------------------------------------------------------------------
# EXPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------

# --------------
# BATCH EXPORTER
# --------------
@getresponse
class GrTagBatchExporter(BatchExporter):
    _model_name = ['getresponse.gr.tag']

    def batch_run(self, domain=None, fields=None, delay=False, **kwargs):
        domain = domain if isinstance(domain, list) else []

        # SEARCH FOR RECORDS NOT LINKED TO A BINDING RECORD
        # ATTENTION: You must use None for the search domain (instead of False)
        original_odoo_model = self.binder.unwrap_model()
        tags = self.env[original_odoo_model].search(domain)
        tags_without_binding = tags.filtered(lambda r: not r.getresponse_bind_ids)

        # CREATE A BINDING BEFORE THE EXPORT
        for tag in tags_without_binding:
            binding_vals = {
                self.binder._backend_field: self.backend_record.id,
                self.binder._openerp_field: tag.id
            }
            binding = self.env[self.model._name].create(binding_vals)
            _logger.info("Created binding for '%s' before batch export! (binding: %s %s, vals: %s)"
                         "" % (original_odoo_model, binding._name, binding.id, binding_vals)
                         )

        # SINCE ALL BINDINGS EXIST NOW WE CAN CALL THE ORIGINAL batch_run()
        return super(GrTagBatchExporter, self).batch_run(domain=domain, fields=fields, delay=delay, **kwargs)


@job(default_channel='root.getresponse')
def gr_tag_export_batch(session, model_name, backend_id, domain=None, fields=None, delay=False, **kwargs):
    """ Prepare the batch export of tag definitions to GetResponse """
    connector_env = get_environment(session, model_name, backend_id)

    # Get the exporter connector unit
    batch_exporter = connector_env.get_connector_unit(GrTagBatchExporter)

    # Start the batch export
    batch_exporter.batch_run(domain=domain, fields=fields, delay=delay, **kwargs)


# ----------------------
# SINGLE RECORD EXPORTER
# ----------------------
# In this class we could alter the generic GetResponse export sync flow We could overwrite all the methods from the
# shared GetResponseExporter here if needed!
@getresponse
class GrTagExporter(GetResponseExporter):
    _model_name = ['getresponse.gr.tag']

    _base_mapper = GrTagExportMapper


# -----------------------------
# SINGLE RECORD DELETE EXPORTER
# -----------------------------
@getresponse
class GrTagDeleteExporter(GetResponseDeleteExporter):
    _model_name = ['getresponse.gr.tag']

