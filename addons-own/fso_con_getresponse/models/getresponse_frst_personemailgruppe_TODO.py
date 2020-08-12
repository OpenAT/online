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
#     - TODO: CREATION OF BINDING RECORDS
#       create a binding record on record creation of the unwrapped model
#     - TODO: FIRING OF EVENTS
#       Call consumer functions on events like @on_record_create and alike
#
# The importers and exporters are in separate files!
# TODO: Custom Fields must be synced and created first for all contact fields needed!
# TODO: Custom Tags Model and sync of custom Tag definition
# TODO: Find out what would work best for partner > PersonEmail > Personemailgrupp to contact model
# ----------------
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

from .backend import getresponse
from .unit_adapter import GetResponseCRUDAdapter
from .unit_binder import GetResponseBinder

import re


# ------------------------------------------
# CONNECTOR BINDING MODEL AND ORIGINAL MODEL
# ------------------------------------------
# WARNING: When using delegation inheritance, methods are not inherited, only fields!
class GetResponseContact(models.Model):
    _name = 'getresponse.frst.personemailgruppe'
    _inherits = {'frst.personemailgruppe': 'odoo_id'}
    _description = 'GetResponse Contact (Subscription) Binding'

    backend_id = fields.Many2one(
        comodel_name='getresponse.backend',
        string='GetResponse Connector Backend',
        required=True,
        readonly=True,
        ondelete='restrict'
    )
    odoo_id = fields.Many2one(
        comodel_name='frst.personemailgruppe',
        string='Fundraising Studio Subscription',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    getresponse_id = fields.Char(
        string='GetResponse Contact ID',
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
    _inherit = 'frst.personemailgruppe'

    getresponse_bind_ids = fields.One2many(
        comodel_name='getresponse.frst.personemailgruppe',
        inverse_name='odoo_id',
    )


# ----------------
# CONNECTOR BINDER
# ----------------
# Nothing to do here since no modifications to the generic binder implementation are needed
# Just make sure to add all binding models to the '_model_name' list of the GetResponseBinder class
# HINT: Check unit_binder.py > GetResponseBinder()


# -----------------
# CONNECTOR ADAPTER
# -----------------
# The Adapter is a subclass of an ConnectorUnit class. The ConnectorUnit Object holds information about the
# connector_env, the backend, the backend_record and about the connector session
@getresponse
class PersonemailgruppeAdapter(GetResponseCRUDAdapter):
    """
    ATTENTION: read() and search_read() will return a dict and not the getresponse_record itself but
               create() and write() will return a getresponse object from the getresponse-python lib!
    """
    _model_name = 'getresponse.frst.personemailgruppe'
    _getresponse_model = 'contact'

    # TODO: add fields to get_all_contacts to search only for the ids of the contacts
    def search(self, campaign_ids=None, **kwargs):
        """ Returns a list of GetResponse contact ids """
        assert isinstance(campaign_ids, list), "campaign_ids must be a list"
        assert len(campaign_ids) >= 1, "Select at least one campaign to search for contacts"
        contacts = self.get_all_contacts(campaign_ids=campaign_ids, **kwargs)
        return [contact.id for contact in contacts]

    # TODO
    def read(self, id, attributes=None):
        """ Returns the information of one record found by the external record id as a dict """
        campaign = self.getresponse_api_session.get_campaign(id, params=attributes)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaign.__dict__

    # TODO
    def search_read(self, filters=None):
        """ Search records based on 'filters' and return their information as a dict """
        campaigns = self.getresponse_api_session.get_campaigns(filters)
        # WARNING: A dict() is expected! Right now 'campaign' is a campaign object!
        return campaigns.__dict__

    # TODO
    def create(self, data):
        campaign = self.getresponse_api_session.create_campaign(data)
        # WARNING: !!! We return the campaign object an not a dict !!!
        return campaign

    # TODO
    def write(self, id, data):
        campaign = self.getresponse_api_session.update_campaign(id, body=data)
        # WARNING: !!! We return the campaign object and not a dict !!!
        return campaign

    # TODO
    def delete(self, id):
        raise NotImplementedError
