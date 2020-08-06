# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ImportMapper, ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job

from .helper_connector import get_environment
from .backend import getresponse

from .unit_adapter import GetResponseCRUDAdapter
from .unit_import import GetResponseImporter, DelayedBatchImporter, DirectBatchImporter


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
        ('name', 'gruppe_lang'),
        ('name', 'gruppe_kurz'),
        ('language_code', 'gr_language_code')
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def getresponse_id(self, record):
        return {'getresponse_id': record['id']}

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
class ZgruppedetailDirectBatchImporter(DirectBatchImporter):
    _model_name = ['getresponse.frst.zgruppedetail']


@job(default_channel='root.getresponse')
def zgruppedetail_import_batch_direct(session, model_name, backend_id, filters=None):
    """ Prepare the batch import of all GetResponse campaigns """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    # ZgruppedetailDirectBatchImporter > DirectBatchImporter._import_record > import_record() which will start:
    #     env.get_connector_unit(GetResponseImporter).run()
    importer = env.get_connector_unit(ZgruppedetailDirectBatchImporter)
    importer.run(filters=filters)


@getresponse
class ZgruppedetailDelayedBatchImporter(DelayedBatchImporter):
    _model_name = ['getresponse.frst.zgruppedetail']


@job(default_channel='root.getresponse')
def zgruppedetail_import_batch_delay(session, model_name, backend_id, filters=None):
    """ Prepare the batch import of all GetResponse campaigns """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    # ZgruppedetailDelayedBatchImporter > DelayedBatchImporter._import_record > import_record.delay() which will start:
    #     env.get_connector_unit(GetResponseImporter).run()
    importer = env.get_connector_unit(ZgruppedetailDelayedBatchImporter)
    importer.run(filters=filters)


# ---------------------------
# IMPORT A GETRESPONSE RECORD
# ---------------------------
# In this class we could alter the generic GetResponse import sync flow for 'getresponse.frst.zgruppedetail'
# HINT: We could overwrite all the methods from the shared GetResponseImporter here if needed!
@getresponse
class ZgruppedetailImporter(GetResponseImporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    _base_mapper = ZgruppedetailImportMapper

    # # This seems not neede at all ?!?
    # def __init__(self, connector_env):
    #     """
    #     :param connector_env: current environment (backend, session, ...)
    #     :type connector_env: :class:`connector.connector.ConnectorEnvironment`
    #     """
    #     super(ZgruppedetailImporter, self).__init__(connector_env)
