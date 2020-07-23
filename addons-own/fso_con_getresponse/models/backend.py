from openerp import fields, models, api
import openerp.addons.connector.backend as backend

# Global variables to make the backend globally available
getresponse = backend.Backend('getresponse')
""" Generic GetResponse Backend """

getresponse_v3 = backend.Backend(parent=getresponse, version='v3')
""" GetResponse Backend for API version 3.0 """


# New model to hold all settings for the getresponse connector
# Also responsible to return the requested version of the backend. Lists all available versions in the field 'version'
class CoffeeBackend(models.Model):
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
