# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# ----------------
# This implements:
#     - THE BINDING ODOO MODEL (delegated inheritance)
#       Holds the external id and internal id as well as additional fields/info not needed in the inherited models
#     - THE BINDER
#       Methods to get the odoo record based on the getresponse id and vice versa
#     - THE ADAPTER
#       Send or get data from the getresponse api, implements the CRUD methods and searching
#
# The importers and exporters are in separate files:
# getresponse_frst_zgruppedetail_import.py, getresponse_frst_zgruppedetail_export.py
# ----------------
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.unit.mapper import ImportMapper, ExportMapper, mapping, only_create
from openerp.addons.connector.queue.job import job

from .helper_connector import get_environment
from .backend import getresponse

from .unit_adapter import GetResponseCRUDAdapter
from .unit_import import GetResponseImporter, DelayedBatchImporter, DirectBatchImporter


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseCampaign(models.Model):
    _name = 'getresponse.frst.zgruppedetail'
    _inherits = {'frst.zgruppedetail': 'odoo_id'}
    _description = 'GetResponse Campaign (List)'

    backend_id = fields.Many2one(
        comodel_name='getresponse.backend',
        string='GetResponse Connector Backend',
        required=True,
        readonly=True,
        ondelete='restrict'
    )
    odoo_id = fields.Many2one(
        comodel_name='frst.zgruppedetail',
        string='Fundraising Studio Group',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    getresponse_id = fields.Char(
        string='GetResponse Campaing ID',
        readonly=True
    )
    sync_date = fields.Datetime(
        string='Last synchronization date',
        readonly=True)

    # ATTENTION: This will be filled/set by the generic binder bind() method in unit_binder.py!
    #            We use this data to check for concurrent writes
    sync_data = fields.Char(
        string='Last synchronization data',
        readonly=True)

    # This constraint is very important for the multithreaded conflict resolution - needed in every binding model!
    _sql_constraints = [
        ('getresponse_uniq', 'unique(backend_id, getresponse_id)',
         'A binding already exists with the same GetResponse ID for this GetResponse backend (Account).'),
    ]


class GetResponseFrstZgruppedetail(models.Model):
    _inherit = 'frst.zgruppedetail'

    getresponse_bind_ids = fields.One2many(
        comodel_name='getresponse.frst.zgruppedetail',
        inverse_name='odoo_id',
    )

    sync_with_getresponse = fields.Boolean(string="Sync with GetResponse",
                                           help="If set the contacts/subscribers of this group/campaign will be"
                                                "synced with GetResponse")

    gr_language_code = fields.Char(string="GetResponse Language Code", readonly=True)
    gr_optin_email = fields.Selection(string="GetResponse OptIn Email", readonly=True,
                                      selection=[('single', 'single'), ('double', 'double')])
    gr_optin_api = fields.Selection(string="GetResponse OptIn API", readonly=True,
                                    selection=[('single', 'single'), ('double', 'double')])
    gr_optin_import = fields.Selection(string="GetResponse OptIn Import", readonly=True,
                                       selection=[('single', 'single')])
    gr_optin_webform = fields.Selection(string="GetResponse OptIn Webform", readonly=True,
                                        selection=[('single', 'single'), ('double', 'double')])

    @api.constrains('sync_with_getresponse', 'zgruppe_id')
    def constrain_sync_with_getresponse(self):
        for r in self:
            if r.sync_with_getresponse:
                # Only E-Mail groups can be enabled to sync with GetResponse
                if not r.zgruppe_id.tabellentyp_id == '100110':
                    raise ValidationError(_("Only groups of type e-mail can be synced with GetResponse!"))
                # TODO: Do not allow to unset 'sync_with_getresponse' as long as PersonEmailGruppe bindings to
                #       GetResponse contacts exists (= as long as synced subscriber exist)

# ----------------
# CONNECTOR BINDER
# ----------------
# Nothing to do here since no modifications to the generic binder implementation are needed
# Just make sure to add all binding models to the '_model_name' list of the GetResponseModelBinder class
# HINT: Check unit_binder.py > GetResponseModelBinder()


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
        campaigns = self.getresponse_api_session.get_campaigns(filters)
        return [campaign.id for campaign in campaigns]

    def read(self, id, attributes=None):
        """ Returns the information of a record  """
        campaign = self.getresponse_api_session.get_campaign(id, params=attributes)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaign.__dict__

    def search_read(self, filters=None):
        """ Search records based on 'filters' and return their information"""
        campaigns = self.getresponse_api_session.get_campaigns(filters)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaigns.__dict__

    def create(self, data):
        campaign = self.getresponse_api_session.create_campaign(data)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaign.__dict__

    def write(self, id, data):
        campaign = self.getresponse_api_session.update_campaign(id, body=data)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaign.__dict__

    # TODO
    def delete(self, id):
        raise NotImplementedError
