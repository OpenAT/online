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
class CampaignImportMapper(ImportMapper):
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

    # ('source: getresponse-python object field', 'target: odoo field')
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


# ---------------------------------------------------------------------------------------------------------------------
# IMPORT SYNCHRONIZER(S)
# ---------------------------------------------------------------------------------------------------------------------

# --------------
# BATCH IMPORTER
# --------------
@getresponse
class CampaignBatchImporter(BatchImporter):
    _model_name = ['getresponse.frst.zgruppedetail']


@job(default_channel='root.getresponse')
def campaign_import_batch(session, model_name, backend_id, filters=None, delay=False, **kwargs):
    """ Prepare the batch import of all GetResponse campaigns """
    if filters is None:
        filters = {}
    connector_env = get_environment(session, model_name, backend_id)

    # Get the import connector unit
    importer = connector_env.get_connector_unit(CampaignBatchImporter)

    # Start the batch import
    importer.batch_run(filters=filters, delay=delay, **kwargs)


# ----------------------
# IMPORT A SINGLE RECORD
# ----------------------
# In this class we could alter the generic GetResponse import sync flow for 'getresponse.frst.zgruppedetail'
# HINT: We could overwrite all the methods from the shared GetResponseImporter here if needed!
@getresponse
class CampaignImporter(GetResponseImporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    _base_mapper = CampaignImportMapper

    def bind_before_import(self):
        binding = self.binding_record
        # Skipp bind_before_import() because a binding was already found for the getresponse_id.
        if binding:
            return binding

        # The record data read from GetResponse as a dict()
        map_record = self._get_map_record()

        # Odoo update data (vals dict for odoo fields)
        odoo_update_data = self._update_data(map_record)

        # The external id from the getresponse record data dict
        getresponse_id = self.getresponse_id

        # The unique custom field definition name
        getresponse_campaign_name = odoo_update_data['gr_name']

        # The backend id
        backend_id = self.backend_record.id

        # EXISTING PREPARED BINDING (binding without external id)
        prepared_binding = self.model.search([('backend_id', '=', backend_id),
                                              ('gr_name', '=', getresponse_campaign_name)])
        if prepared_binding:
            assert len(prepared_binding) == 1, 'More than one binding found for this campaign name!'
            assert not prepared_binding.getresponse_id, 'Prepared binding has a getresponse_id?'
            self.binder.bind(getresponse_id, prepared_binding.id)
            return prepared_binding

        # EXISTING GROUP WITH THIS CAMPAIGN NAME (WITHOUT BINDING)
        unwrapped_model = self.binder.unwrap_model()
        custom_field = self.env[unwrapped_model].search([('gr_name', '=', getresponse_campaign_name)])
        if custom_field:
            assert len(custom_field) == 1, "More than one campaign (zgruppedetail) with this name found!"
            prepared_binding = self.binder._prepare_binding(custom_field.id)
            self.binder.bind(getresponse_id, prepared_binding.id)
            return prepared_binding

        # Nothing found so we return the original method result
        return super(CampaignImporter, self).bind_before_import()
