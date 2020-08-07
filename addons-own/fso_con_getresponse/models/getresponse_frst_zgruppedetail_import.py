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
class ZgruppedetailImportMapper(ImportMapper):
    """ Map all the fields of the the GetResponse API library campaign object to the odoo record fields.
    You can find all all available fields here: ..../getresponse-python/getresponse/campaign.py

    ATTENTION: The field names of the  GetResponse API library (getresponse-python) may not match the field names
               found in the getresponse API documentation e.g. Campaign.language_code is 'languageCode' in the api.
               The final transformation to the correct API names is done by the getresponse-python lib. Check
               _create() from getresponse-python > campaign.py to see the final transformations
    """
    _model_name = 'getresponse.frst.zgruppedetail'

    # TODO: Check if this method may be the correct one for PersonEmail and Partner for PersonEmailGruppe"
    def _map_children(self, record, attr, model):
        pass

    # (getresponse_field_name, odoo_field_name)
    direct = [
        ('name', 'gr_name'),
        ('language_code', 'gr_language_code')
    ]

    @mapping
    def backend_id(self, record):
        # TODO: Get the field name '_openerp_field' from the binder for 'getresponse.frst.zgruppedetail'
        return {'backend_id': self.backend_record.id}

    @mapping
    def getresponse_id(self, record):
        # TODO: Get the field name '_openerp_field' from the binder for 'getresponse.frst.zgruppedetail'
        return {'getresponse_id': record['id']}

    @only_create
    @mapping
    def gruppe_lang(self, record):
        return {'gruppe_lang': record['name'],
                'gruppe_kurz': record['name']}

    @only_create
    @mapping
    def geltungsbereich(self, record):
        return {'geltungsbereich': 'local'}

    @only_create
    @mapping
    def zgruppe_id(self, record):
        # get 'default_zgruppe_id' from the getresponse backend
        return {'zgruppe_id': self.backend_record.default_zgruppe_id.id}

    # OptIn
    @mapping
    def gr_optin_email(self, record):
        return {'gr_optin_email': record['opting_types']['email']}

    @mapping
    def gr_optin_api(self, record):
        return {'gr_optin_api': record['opting_types']['api']}

    @mapping
    def gr_optin_import(self, record):
        return {'gr_optin_import': record['opting_types']['import']}

    @mapping
    def gr_optin_webform(self, record):
        return {'gr_optin_webform': record['opting_types']['webform']}


# ---------------------------------
# CONNECTOR IMPORTER (SYNCHRONIZER)
# ---------------------------------

# -------------------------------------------------------------------------
# SEARCH FOR RECORDS AND START THE IMPORT FOR EACH RECORD DELAYED OR DIRECT
# -------------------------------------------------------------------------
@getresponse
class ZgruppedetailBatchImporter(BatchImporter):
    _model_name = ['getresponse.frst.zgruppedetail']


@job(default_channel='root.getresponse')
def zgruppedetail_import_batch(session, model_name, backend_id, filters=None, delay=False, **kwargs):
    """ Prepare the batch import of all GetResponse campaigns """
    if filters is None:
        filters = {}
    connector_env = get_environment(session, model_name, backend_id)

    # Get the import connector unit
    importer = connector_env.get_connector_unit(ZgruppedetailBatchImporter)

    # Start the batch import
    importer.batch_run(filters=filters, delay=delay, **kwargs)


# ---------------------------
# IMPORT A GETRESPONSE RECORD
# ---------------------------
# In this class we could alter the generic GetResponse import sync flow for 'getresponse.frst.zgruppedetail'
# HINT: We could overwrite all the methods from the shared GetResponseImporter here if needed!
@getresponse
class ZgruppedetailImporter(GetResponseImporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    _base_mapper = ZgruppedetailImportMapper

    # TODO: Find existing groups and bind them before the import if not bound already
    # Because of this you can bind existing GetResponse Campaigns to Existing Groups if you set the gr_name
    # correctly before the import!
    def _get_binding(self):
        bind_record = super(ZgruppedetailImporter, self)._get_binding()

        # Search for an existing Group
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

