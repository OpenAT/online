from openerp import fields, models, api
from openerp.addons.connector.session import ConnectorSession

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