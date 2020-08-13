# -*- coding: utf-8 -*-
from openerp import fields, models, api
from openerp.addons.connector.session import ConnectorSession
from openerp.tools.translate import _

from .getresponse_frst_zgruppedetail_import import zgruppedetail_import_batch
from .getresponse_frst_zgruppedetail_export import zgruppedetail_export_batch

from .getresponse_gr_custom_field_export import gr_custom_field_export_batch

from .getresponse_gr_tag_import import gr_tag_import_batch
from .getresponse_gr_tag_export import gr_tag_export_batch


# New model to hold all settings for the getresponse connector
# Also responsible to return the requested version of the backend. Lists all available versions in the field 'version'
class GetResponseBackend(models.Model):
    _name = 'getresponse.backend'
    _description = 'Getresponse Backend'
    _inherit = 'connector.backend'

    _backend_type = 'getresponse'

    @api.model
    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [('v3', 'GetResponse API v3.0')]

    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )
    api_key = fields.Char(string='GetResponse API Key')

    # Currently this is statically set in the getresponse-python client lib
    #api_url = fields.Char(string='GetResponse API URL')

    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        required=True,
        default=lambda self: self.default_default_lang_id()
    )

    # For GetResponse Campaign import (campaigns created in GetResponse)
    default_zgruppe_id = fields.Many2one(comodel_name="frst.zgruppe", inverse_name='getresponse_backend_ids',
                                         string='Default Group Folder for Campaigns',
                                         ondelete='set null',
                                         help="Create local groups in this folder for campaigns created in GetResponse."
                                              " If this is not set a checkpoint job is created at campaign import!")

    # TODO: subscription settings - this needs to be implemented in the getresponse client as well as in the
    #       frst.zgruppedetail model or maybe just in the backend as a global config?
    #       Check also: class ZgruppedetailImportMapper(ImportMapper)

    # ----------
    # CONSTRAINS
    # ----------
    @api.constrains('default_zgruppe_id')
    def constraint_default_zgruppe_id(self):
        for r in self:
            if r.default_zgruppe_id:
                assert r.default_zgruppe_id.tabellentyp_id == '100110', _(
                    "The 'Default-Group-Folder' type must be 'Email'!")

    @api.constrains('default_lang_id')
    def constraint_default_lang_id(self):
        for r in self:
            assert r.default_lang_id.code == 'de_DE', "Only german 'de_DE' is supported!"

    # --------
    # DEFAULTS
    # --------
    @api.model
    def default_default_lang_id(self):
        german_lang = self.env['res.lang'].search([('code', '=', 'de_DE')], limit=1)
        return german_lang if len(german_lang) == 1 else False

    # ------------------------
    # IMPORT CAMPAIGNS BUTTONS
    # ------------------------
    @api.multi
    def import_getresponse_campaigns_direct(self):
        """ Import all campaigns from getresponse as frst.zgruppedetail """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            zgruppedetail_import_batch(session, 'getresponse.frst.zgruppedetail', backend.id, delay=False)

    @api.multi
    def import_getresponse_campaigns_delay(self):
        """ Import all campaigns from getresponse as frst.zgruppedetail delayed (connector jobs) """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            zgruppedetail_import_batch.delay(session, 'getresponse.frst.zgruppedetail', backend.id, delay=True)

    # ------------------------
    # EXPORT CAMPAIGNS BUTTONS
    # ------------------------
    @api.multi
    def export_getresponse_campaigns_direct(self):
        """ Export all frst.zgruppedetail groups with sync_with_getresponse=True to getresponse campaigns """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            zgruppedetail_export_batch(session, 'getresponse.frst.zgruppedetail', backend.id, delay=False)

    @api.multi
    def export_getresponse_campaigns_delay(self):
        """ Export all frst.zgruppedetail groups with sync_with_getresponse=True delayed (connector jobs)
        to getresponse campaigns """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            zgruppedetail_export_batch.delay(session, 'getresponse.frst.zgruppedetail', backend.id, delay=True)

    # ----------------------------
    # TODO: IMPORT CUSTOM FIELDS BUTTONS
    # ----------------------------

    # ----------------------------
    # EXPORT CUSTOM FIELDS BUTTONS
    # ----------------------------
    @api.multi
    def export_getresponse_custom_fields_direct(self):
        """ Export all gr.custom_field field definitions to GetResponse """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            gr_custom_field_export_batch(session, 'getresponse.gr.custom_field', backend.id, delay=False)

    @api.multi
    def export_getresponse_custom_fields_delay(self):
        """ Export all gr.custom_field field definitions to GetResponse delayed (connector jobs) """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            gr_custom_field_export_batch.delay(session, 'getresponse.gr.custom_field', backend.id, delay=True)

    # -------------------
    # IMPORT TAGS BUTTONS
    # -------------------
    @api.multi
    def import_getresponse_tags_direct(self):
        """ Import all tags from getresponse """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            gr_tag_import_batch(session, 'getresponse.gr.tag', backend.id, delay=False)

    @api.multi
    def import_getresponse_tags_delay(self):
        """ Import all tags from getresponse delayed (connector jobs) """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            gr_tag_import_batch.delay(session, 'getresponse.gr.tag', backend.id, delay=True)

    # -------------------
    # EXPORT TAGS BUTTONS
    # -------------------
    @api.multi
    def export_getresponse_tags_direct(self):
        """ Export all gr.tag field definitions to GetResponse """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            gr_tag_export_batch(session, 'getresponse.gr.tag', backend.id, delay=False)

    @api.multi
    def export_getresponse_tags_delay(self):
        """ Export all gr.tag field definitions to GetResponse delayed (connector jobs) """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            gr_tag_export_batch.delay(session, 'getresponse.gr.tag', backend.id, delay=True)


# Inverse field for the default_zgruppe_id settings field in the backend
class FRSTzGruppe(models.Model):
    _inherit = 'frst.zgruppe'

    getresponse_backend_ids = fields.One2many(comodel_name="getresponse.backend", inverse_name='default_zgruppe_id',
                                              string="GetResponse Backend IDS")
