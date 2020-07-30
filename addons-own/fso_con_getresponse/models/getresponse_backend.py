from openerp import fields, models, api
from openerp.addons.connector.session import ConnectorSession
from openerp.tools.translate import _

from .getresponse_zgruppedetail import zgruppedetail_import_batch_delay, zgruppedetail_import_batch_direct


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
    #api_url = fields.Char(string='GetResponse API URL') # Currently this is directly set in the getresponse-python client lib
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
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

    @api.constrains('default_zgruppe_id')
    def constraint_default_zgruppe_id(self):
        for r in self:
            if r.default_zgruppe_id:
                assert r.default_zgruppe_id.tabellentyp_id == '100110', _(
                    "The 'Default Group Folder' type must be 'Email'!")

    @api.multi
    def import_getresponse_campaigns_delay(self):
        """ Import all campaigns from getresponse as frst.zgruppedetail """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            zgruppedetail_import_batch_delay.delay(session, 'getresponse.frst.zgruppedetail', backend.id, filters=None)

    @api.multi
    def import_getresponse_campaigns_direct(self):
        """ Import all campaigns from getresponse as frst.zgruppedetail """
        session = ConnectorSession(self.env.cr, self.env.uid, context=self.env.context)
        for backend in self:
            zgruppedetail_import_batch_direct(session, 'getresponse.frst.zgruppedetail', backend.id, filters=None)


class FRSTzGruppe(models.Model):
    _inherit = 'frst.zgruppe'

    getresponse_backend_ids = fields.One2many(comodel_name="getresponse.backend", inverse_name='default_zgruppe_id',
                                              string="GetResponse Backend IDS")
