# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import models, fields
from openerp.addons.connector.unit.mapper import ImportMapper, ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job

from .connector import get_environment
from .backend import getresponse

from .unit_adapter import GetResponseCRUDAdapter
from .unit_synchronizer_import import GetResponseImporter, DelayedBatchImporter


# -----------------------
# CONNECTOR BINDING MODEL
# -----------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseCampaign(models.Model):
    _name = 'getresponse.frst.zgruppedetail'
    _inherits = {'frst.zgruppedetail': 'odoo_id'}
    _description = 'GetResponse Campaign (List)'

    backend_id = fields.Many2one(
        comodel_name='getresponse.backend',
        string='GetResponse Connector Backend',
        required=True,
        ondelete='restrict'
    )
    odoo_id = fields.Many2one(
        comodel_name='frst.zgruppedetail',
        string='Fundraising Studio Group',
        required=True,
        ondelete='cascade'
    )
    getresponse_id = fields.Char(
        string='GetResponse Campaing ID',
        readonly=True
    )

    sync_date = fields.Datetime(string='Last synchronization date', readonly=True)
    sync_data = fields.Char(string='Last synchronization data', readonly=True)

    _sql_constraints = [
        ('getresponse_uniq', 'unique(backend_id, getresponse_id)',
         'A binding already exists with the same GetResponse ID.'),
    ]


class GetResponseFrstZgruppedetail(models.Model):
    _inherit = 'frst.zgruppedetail'

    getresponse_bind_ids = fields.One2many(
        comodel_name='getresponse.frst.zgruppedetail',
        inverse_name='odoo_id',
    )


# ----------------
# CONNECTOR BINDER
# ----------------
# Nothing to do here since no modifications to the generic binder implementation are needed
# Just make sure to add all binding models to the '_model_name' list of the GetResponseModelBinder class
# Check unit_binder.py > GetResponseModelBinder()


# -----------------
# CONNECTOR ADAPTER
# -----------------
# The Adapter is a subclass of an ConnectorUnit class. The ConnectorUnit Object holds information about the
# connector_env, the backend, the backend_record and about the connector session
@getresponse
class ZgruppedetailAdapter(GetResponseCRUDAdapter):
    _model_name = 'getresponse.frst.zgruppedetail'
    _getresponse_model = 'campaign'

    def search(self, filters=None):
        """ Returns a list of GetResponse campaign ids """
        assert not filters or isinstance(filters, dict), "filters must be a dict!"
        campaigns = self.getresponse.get_campaigns(filters)
        return [campaign.id for campaign in campaigns]

    def read(self, id, attributes=None):
        """ Returns the information of a record  """
        campaign = self.getresponse.get_campaign(id, params=attributes)
        # TODO: Check if a dict() is expected! Right now we return a campaign object!
        return campaign

    def search_read(self, filters=None):
        """ Search records based on 'filters' and return their information"""
        campaigns = self.getresponse.get_campaigns(filters)
        # TODO: Check if a dict() is expected! Right now we return a campaign object!
        return campaigns

    def create(self, data):
        campaign = getresponse.create_campaign(data)
        # TODO: Check if a dict() is expected! Right now we return a campaign object!
        return campaign

    def write(self, id, data):
        campaign = self.getresponse.update_campaign(id, body=data)
        return campaign

    def delete(self, id):
        raise NotImplementedError


# ----------------
# CONNECTOR MAPPER
# ----------------
# Transform the data from GetResponse campaing objects to odoo records and vice versa
@getresponse
class ZgruppedetailImportMapper(ImportMapper):
    _model_name = 'getresponse.frst.zgruppedetail'

    # (getresponse_field_name, odoo_field_name)
    direct = [
        ('name', 'name')
    ]

    def _map_children(self, record, attr, model):
        pass

    # TODO: subscription settings - this needs to be implemented in the getresponse client as well as in the
    #       frst.zgruppedetail model or maybe just in the backend as a global config?


# ---------------------------------
# CONNECTOR IMPORTER (SYNCHRONIZER)
# ---------------------------------
@getresponse
class ZgruppedetailImporter(GetResponseImporter):
    _model_name = ['getresponse.frst.zgruppedetail']

    _base_mapper = ZgruppedetailImportMapper

    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(ZgruppedetailImporter, self).__init__(connector_env)

    # ATTENTION: We could overwrite all the methods from GetResponseImporter here if needed


@getresponse
class ZgruppedetailDelayedBatchImporter(DelayedBatchImporter):
    _model_name = ['getresponse.frst.zgruppedetail']


@job(default_channel='root.getresponse')
def zgruppedetail_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the batch import of all campaigns modified or created in GetResponse """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(ZgruppedetailDelayedBatchImporter)
    importer.run(filters=filters)
