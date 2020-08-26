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
# ----------------
import re
from getresponse.excs import NotFoundError

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from openerp.addons.connector.event import on_record_create, on_record_write, on_record_unlink
from openerp.addons.connector.exception import IDMissingInBackend

from .backend import getresponse
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseCampaign(models.Model):
    _name = 'getresponse.frst.zgruppedetail'
    _inherits = {'frst.zgruppedetail': 'odoo_id'}
    _description = 'GetResponse Campaign (List) Binding'

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
    gr_name = fields.Char(string='GetResponse Campaign Name',
                          help="GetResponse will ony accept campaign names "
                               "consisting of '0-9' 'a-z' and '_'. If a group uses a name "
                               "not compatible with GetResponse you may choose an alternative "
                               "name for GetResponse here!")
    gr_language_code = fields.Char(string="GetResponse Language Code", readonly=True)
    gr_optin_email = fields.Selection(string="GetResponse OptIn Email", readonly=True,
                                      selection=[('single', 'single'), ('double', 'double')])
    gr_optin_api = fields.Selection(string="GetResponse OptIn API", readonly=True,
                                    selection=[('single', 'single'), ('double', 'double')])
    gr_optin_import = fields.Selection(string="GetResponse OptIn Import", readonly=True,
                                       selection=[('single', 'single')])
    gr_optin_webform = fields.Selection(string="GetResponse OptIn Webform", readonly=True,
                                        selection=[('single', 'single'), ('double', 'double')])

    # This may be better placed in the binding model and combined with the backend_id BUT for now synchronisation
    # to multiple backends (GetResponse Accounts) is not supported anyway ;)
    _sql_constraints = [
        ('gr_name_uniq', 'unique(gr_name)', 'A group already exists with the same GetResponse Campaign Name'),
    ]

    @api.constrains('sync_with_getresponse', 'zgruppe_id', 'gruppe_lang', 'gruppe_kurz')
    def constrain_sync_with_getresponse(self):
        for r in self:
            if r.sync_with_getresponse:
                # Only E-Mail groups can be enabled to sync with GetResponse
                if not r.zgruppe_id.tabellentyp_id == '100110':
                    raise ValidationError(_("Only groups of type e-mail can be synced with GetResponse!"))
                # Check the group name
                if not r.gr_name:
                    name = r.gruppe_lang or r.gruppe_kurz
                    assert re.match(r"(?:[a-z0-9_]+)\Z", name, flags=0), _(
                        "Only a-z, 0-9 and _ is allowed for the GetResponse campaign name '{}'! "
                        "Please change the group name or use the 'GetResponse Campaign Name' field!").format(name)
                # TODO: Do not allow to unset 'sync_with_getresponse' as long as PersonEmailGruppe bindings to
                #       GetResponse contacts exists (= as long as synced subscriber exist)

    @api.constrains('gr_name')
    def constrain_gr_name(self):
        for r in self:
            if r.gr_name:
                assert re.match(r"(?:[a-z0-9_]+)\Z", r.gr_name, flags=0), _(
                    "Only a-z, 0-9 and _ is allowed for the GetResponse campaign name: '{}'").format(r.gr_name)


# ----------------
# CONNECTOR BINDER
# ----------------
@getresponse
class ZgruppedetailBinder(GetResponseBinder):
    _model_name = 'getresponse.frst.zgruppedetail'

# -----------------
# CONNECTOR ADAPTER
# -----------------
# The Adapter is a subclass of an ConnectorUnit class. The ConnectorUnit Object holds information about the
# connector_env, the backend, the backend_record and about the connector session
@getresponse
class ZgruppedetailAdapter(GetResponseCRUDAdapter):
    """
    ATTENTION: read() and search_read() will return a dict and not the getresponse_record itself but
               create() and write() will return a getresponse object from the getresponse-python lib!
    """
    _model_name = 'getresponse.frst.zgruppedetail'
    _getresponse_model = 'campaigns'

    def search(self, filters=None):
        """ Returns a list of GetResponse campaign ids """
        assert not filters or isinstance(filters, dict), "filters must be a dict!"
        campaigns = self.getresponse_api_session.get_campaigns(filters)
        return [campaign.id for campaign in campaigns]

    def read(self, id, attributes=None):
        """ Returns the information of one record found by the external record id as a dict """
        try:
            campaign = self.getresponse_api_session.get_campaign(id, params=attributes)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaign.__dict__

    def search_read(self, filters=None):
        """ Search records based on 'filters' and return their information as a dict """
        campaigns = self.getresponse_api_session.get_campaigns(filters)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaigns.__dict__

    def create(self, data):
        campaign = self.getresponse_api_session.create_campaign(data)
        # WARNING: !!! We return the campaign object an not a dict !!!
        return campaign

    def write(self, id, data):
        try:
            campaign = self.getresponse_api_session.update_campaign(id, body=data)
        except NotFoundError as e:
            raise IDMissingInBackend(str(e.message) + ', ' + str(e.response))
        # WARNING: !!! We return the campaign object and not a dict !!!
        return campaign

    # TODO
    def delete(self, id):
        raise NotImplementedError
