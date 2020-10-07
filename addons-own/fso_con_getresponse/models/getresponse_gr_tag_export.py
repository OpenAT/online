# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging
import json

from openerp.addons.connector.unit.mapper import ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.exception import IDMissingInBackend, RetryableJobError

from .helper_connector import get_environment
from .backend import getresponse
from .unit_export import BatchExporter, GetResponseExporter
from .unit_export_delete import GetResponseDeleteExporter

_logger = logging.getLogger(__name__)


# -----------------------
# CONNECTOR EXPORT MAPPER
# -----------------------
@getresponse
class TagExportMapper(ExportMapper):
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
class TagBatchExporter(BatchExporter):
    _model_name = ['getresponse.gr.tag']


@job(default_channel='root.getresponse')
def tag_export_batch(session, model_name, backend_id, domain=None, fields=None, delay=False, **kwargs):
    """ Prepare the batch export of tag definitions to GetResponse """
    connector_env = get_environment(session, model_name, backend_id)

    # Get the exporter connector unit
    batch_exporter = connector_env.get_connector_unit(TagBatchExporter)

    # Start the batch export
    batch_exporter.batch_run(domain=domain, fields=fields, delay=delay, **kwargs)


# ----------------------
# SINGLE RECORD EXPORTER
# ----------------------
# In this class we could alter the generic GetResponse export sync flow We could overwrite all the methods from the
# shared GetResponseExporter here if needed!
@getresponse
class TagExporter(GetResponseExporter):
    _model_name = ['getresponse.gr.tag']

    _base_mapper = TagExportMapper

    def run(self, binding_id, *args, **kwargs):

        # RECORD REMOVED IN GETRESPONSE HANDLING
        try:
            return super(TagExporter, self).run(binding_id, *args, **kwargs)
        except IDMissingInBackend as e:
            # Try to unlink the tag definition in odoo
            if self.binding_record and self.binding_record.getresponse_id:
                tag = self.binder.unwrap_binding(self.binding_record, browse=True)
                if len(tag) == 1:
                    msg = ('TAG DEFINITION %s NOT FOUND IN GETRESPONSE! UNLINKING TAG %s IN ODOO!'
                           '' % (self.binding_record.getresponse_id, tag.id))
                    _logger.warning(msg)
                    tag.with_context(connector_no_export=True).unlink()
                    return msg

            # Raise the exception if we could not unlink the tag definition in odoo
            raise e

        # Raise all other exceptions
        except Exception as e:
            raise e


# -----------------------------
# SINGLE RECORD DELETE EXPORTER
# -----------------------------
@getresponse
class TagDeleteExporter(GetResponseDeleteExporter):
    _model_name = ['getresponse.gr.tag']

