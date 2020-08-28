# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job

from .helper_connector import get_environment
from .backend import getresponse
from .unit_export import BatchExporter, GetResponseExporter
from .unit_export_delete import GetResponseDeleteExporter

import logging
_logger = logging.getLogger(__name__)


# -----------------------
# CONNECTOR EXPORT MAPPER
# -----------------------
@getresponse
class CampaignExportMapper(ExportMapper):
    """ Map all the fields of the odoo record to the GetResponse API field names.

    ATTENTION: !!! FOR THE EXPORT WE MUST USE THE FIELD NAMES OF THE GET RESPONSE API !!!

               When we import data the client lib will return a campaign object. The data of campaign is stored
               in the objects attributes. The pitfall is that the object attributes will follow python conventions so
               the GetResponse 'languageCode' is the attribute campaign.language_code if we read objects from GR.

               BUT for the export to GetResponse (update or write) we need the prepare the "raw data" for the
               request because no campaign object is created by the getresponse python lib :( but only returned
               after the campaing was created!

    ATTENTION: We do NOT map fields that should be set in getresponse only! So OptIn Types or gr_language_code can be
               changed in getresponse only. The only exception from this rule is if we create campaigns from odoo
               zGruppeDetail records where we need to set the defaults on creation time.

   TODO: We need to import the campaign from getresponse after first export to get all the
         getresponse campaign OR use the data from the returned getresponse campaign object to update the odoo record!
    """
    _model_name = 'getresponse.frst.zgruppedetail'

    def _map_children(self, record, attr, model):
        pass

    # ATTENTION: !!! FOR THE EXPORT WE MUST USE THE RAW FIELD NAMES OF THE GET RESPONSE API !!!

    @mapping
    def name(self, record):
        return {'name': record.gr_name or record.gruppe_lang or record.gruppe_kurz}

    @only_create
    @mapping
    def language_code(self, record):
        return {'languageCode': 'DE'}

    # OptIn
    # ATTENTION: We can only export or import contacts (subscribers / PersonEmailGruppe) that are approved. Or in
    #            other words only subscribers where the optin is already done! This is more or less a getresponse
    #            constrain since non approved subscribers are treated like 'deleted' from getresponse and will not be
    #            returned by regular searches!
    #            Therefore we do not sync any PersonEmailGruppe in an state other than 'approved' or 'subscribed'
    #            Because of this  all subscribers created by the api through FSON are subscribed already and we set
    #            'api' to 'single'.
    @only_create
    @mapping
    def opting_types(self, record):
        return {'optinTypes': {
            'api': 'single',
            }
        }


# ---------------------------------------------------------------------------------------------------------------------
# EXPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------

# --------------
# BATCH EXPORTER
# --------------
@getresponse
class CampaignBatchExporter(BatchExporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    def batch_run(self, domain=None, fields=None, delay=False, **kwargs):
        assert domain is None, "You can not set a custom domain for zGruppeDetail batch export runs to GetResponse!"
        domain = [('sync_with_getresponse', '=', True)]

        # SEARCH FOR ENABLED GROUPS IN THE ORIGINAL ODOO MODEL frst.zgruppedetail TO FIND RECORDS WITHOUT A BINDING
        original_odoo_model = self.binder.unwrap_model()
        enabled_frst_groups = self.env[original_odoo_model].search(domain)

        # CREATE A BINDING FOR ALL ENABLED GROUPS BEFORE THE EXPORT RUN
        enabled_frst_groups_without_bindings = enabled_frst_groups.filtered(lambda r: not r.getresponse_bind_ids)
        for frst_group in enabled_frst_groups_without_bindings:
            binding_vals = {
                self.binder._backend_field: self.backend_record.id,
                self.binder._openerp_field: frst_group.id
            }
            binding = self.env[self.model._name].create(binding_vals)
            _logger.info("Created binding for unbound 'GetResponse sync enabled frst.zgruppedetail' before batch"
                         " export! (binding: %s %s, vals: %s)" % (binding._name, binding.id, binding_vals))

        # SINCE ALL BINDINGS EXIST NOW WE CAN CALL THE ORIGINAL batch_run()
        return super(CampaignBatchExporter, self).batch_run(domain=domain, fields=fields, delay=delay, **kwargs)


@job(default_channel='root.getresponse')
def campaign_export_batch(session, model_name, backend_id, domain=None, fields=None, delay=False, **kwargs):
    """ Prepare the batch export of all enabled frst.zgruppedetail to GetResponse campaigns """
    connector_env = get_environment(session, model_name, backend_id)

    # Get the exporter connector unit
    batch_exporter = connector_env.get_connector_unit(CampaignBatchExporter)

    # Start the batch export
    batch_exporter.batch_run(domain=domain, fields=fields, delay=delay, **kwargs)


# ----------------------
# SINGLE RECORD EXPORTER
# ----------------------
# In this class we could alter the generic GetResponse export sync flow for 'getresponse.frst.zgruppedetail'
# HINT: We could overwrite all the methods from the shared GetResponseExporter here if needed!
@getresponse
class CampaignExporter(GetResponseExporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    _base_mapper = CampaignExportMapper


# -----------------------------
# SINGLE RECORD DELETE EXPORTER
# -----------------------------
@getresponse
class CampaignDeleteExporter(GetResponseDeleteExporter):
    _model_name = ['getresponse.frst.zgruppedetail']
