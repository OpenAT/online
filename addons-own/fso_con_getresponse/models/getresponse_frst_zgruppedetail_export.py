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


# -----------------------
# CONNECTOR EXPORT MAPPER
# -----------------------
@getresponse
class ZgruppedetailExportMapper(ExportMapper):
    """ Map all the fields of the odoo record to the GetResponse API library campaign object.
    You can find all all available fields here: ..../getresponse-python/getresponse/campaign.py

    ATTENTION: The field names of the  GetResponse API library (getresponse-python) may not match the field names
               found in the getresponse API documentation e.g. Campaign.language_code is 'languageCode' in the api.
               The final transformation to the correct API names is done by the getresponse-python lib. Check
               _create() from getresponse-python > campaign.py to see the final transformations

    ATTENTION: We do NOT map fields that should be set in getresponse only! So OptIn Types or gr_language_code can be
               changed in getresponse only. The only exception from this rule is if we create campaigns from odoo
               zGruppeDetail records where we need to set the defaults on creation time.
               TODO: Therefore we need to import the campaign from getresponse after first export to get all the
                     getresponse campaign data into odoo
    """

    def _map_children(self, record, attr, model):
        pass

    _model_name = 'getresponse.frst.zgruppedetail'

    @mapping
    def name(self, record):
        return {'name': record.gruppe_lang or record.gruppe_kurz}

    @only_create
    @mapping
    def language_code(self, record):
        return {'language_code': 'DE'}

    # OptIn
    # ATTENTION: We can only export or import contacts (subscribers / PersonEmailGruppe) that are approved. Or in
    #            other words only subscribers where the optin is already done! This is more or less a getresponse
    #            constrain since non approved subscribers are treated like 'deleted' from getresponse and will not be
    #            returned by regular searches!
    #            Therefore do not sync any PersonEmailGruppe in an state other than 'approved' or 'subscribed'
    #            Because of this  all subscribers created by the api through FSON are subscribed already and we set
    #            'api' to 'single'.
    @only_create
    @mapping
    def opting_types(self, record):
        return {'opting_types': {
            'api': 'single',
            }
        }


# ---------------------------------
# CONNECTOR IMPORTER (SYNCHRONIZER)
# ---------------------------------

# -------------------------------------------------------------------------
# SEARCH FOR RECORDS AND START THE IMPORT FOR EACH RECORD DELAYED OR DIRECT
# -------------------------------------------------------------------------
@getresponse
class ZgruppedetailBatchExporter(BatchExporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    def batch_run(self, domain=None, fields=None, delay=False, **kwargs):
        assert domain is None, "You can not set a custom domain for zGruppeDetail batch export runs to GetResponse!"
        domain = [('sync_with_getresponse', '=', True)]

        # SEARCH FOR ENABLED GROUPS IN THE ORIGINAL ODOO MODEL frst.zgruppedetail TO FIND RECORDS WITHOUT A BINDING
        original_odoo_model = self.binder.unwrap_model()
        enabled_frst_groups = self.env[original_odoo_model].search(domain)

        # CREATE A BINDING FOR ALL ENABLED GROUPS
        enabled_frst_groups_without_bindings = enabled_frst_groups.filtered(lambda r: not r.getresponse_bind_ids)
        for frst_group in enabled_frst_groups_without_bindings:
            binding_vals = {
                self.binder._backend_field: self.backend_record.id,
                self.binder._openerp_field: frst_group.id
            }
            binding = self.env[self.model._name].create(binding_vals)

        # SINCE ALL BINDINGS EXIST NOW WE CAN CALL THE ORIGINAL batch_run()
        return super(ZgruppedetailBatchExporter, self).batch_run(domain=domain, fields=fields, delay=delay, **kwargs)


@job(default_channel='root.getresponse')
def zgruppedetail_export_batch(session, model_name, backend_id, delay=False):
    """ Prepare the batch export of all enabled frst.zgruppedetail to GetResponse campaigns """
    connector_env = get_environment(session, model_name, backend_id)

    # Get the exporter connector unit!
    batch_exporter = connector_env.get_connector_unit(ZgruppedetailBatchExporter)

    # Start the batch export
    batch_exporter.batch_run(delay=delay)

# ---------------------------
# EXPORT A GETRESPONSE RECORD
# ---------------------------
# In this class we could alter the generic GetResponse export sync flow for 'getresponse.frst.zgruppedetail'
# HINT: We could overwrite all the methods from the shared GetResponseExporter here if needed!
@getresponse
class ZgruppedetailExporter(GetResponseExporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    _base_mapper = ZgruppedetailExportMapper

