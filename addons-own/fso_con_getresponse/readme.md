# connector concepts
Some of the connector concepts

## backend
Global variables that hold a backend.Backend() object \
e.g. ```getresponse = backend.Backend('getresponse')``` \
or for a specific version of the backend ```getresponse_v3 = backend.Backend(parent=getresponse, version='v3')```

## binding
The binding is the link between an Odoo record and an external record. There is no forced implementation for the 
bindings. The most straightforward techniques are: storing the external ID in the same model (account.invoice), in a 
new link model or in a new link model which _inherits account.invoice. We use the delegation inheritance version
to keep most new fields out of the original odoo model.

## Connector Unit
connector unit is a generic term that sums up all parts needed for the synchronisation of records

### binder
Implementation of the link between the odoo record and the GetResponse Record. 
Will return the getresponse id for an odoo record or vice versa the odoo record id for an getresponse id

### mapper
Transform the records between the systems \
e.g. ```frst.zgruppedetail (odoo) <> campaign (GetResponse)```

### adapter
The adapters (```BackendAdapter```) implements the discussion with the backend's APIs. In this case it uses our custom version of the 
getresponse-python lib.

### synchronizer
 Synchronizer define the flow of a synchronization. It uses the ```binder``` ```mapper``` and ```adapter``` objects for
 it's work. There are three synchronizer classes of interest: ```ExportSynchronizer```. ```ImportSynchronizer``` 
 and  ```DeleteSynchronizer```
 
# The bigger concept
How this all works together.
 
Start with global backend variables and a backend class. The new odoo connector backend model will hold all the fields 
for the access to the external api like ```api_key``` and ```api_url``` as well as generic fields for the syncer 
configuration like ```default_lang```
 
```python
#backend.py
getresponse = backend.Backend('getresponse')
getresponse_v3 = backend.Backend(parent=getresponse, version='v3')

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
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
    )
```

For pure convenience we will add a connector.py and add a function to ease the creation of a new connector environment
```python
#connector.py
def get_environment(session, model_name, backend_id):
    """ Create an environment to work with. """
    backend_record = session.env['getresponse.backend'].browse(backend_id)
    env = Environment(backend_record, session, model_name)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
    if lang_code == session.context.get('lang'):
        return env
    else:
        with env.session.change_context(lang=lang_code):
            return env
```
With this function we can create an odoo connector environment for a record we created in the new 
```getresponse.backend``` odoo model \
e.g. ```getresponse_connector_env = get_environment(session, 'getresponse.frst.zgruppedetail', 1)```

Next we create a Binding. We need to store the external id (getreponse id) somewhere and we need
to make sure the connector unit knows how to transform the getresponse records to internal records and vice versa:

We use delegation inheritance for the binding model (_inherits). 

The binding model stores 
  - a link to the connector backend (record of the odoo model ```getresponse.backend```)
  - a link to the odoo record
  - the id of the external system (getresponse_id)
  
```python
class GetResponseCampaign(models.Model):
    _name = 'getresponse.frst.zgruppedetail'
    _inherits = {'frst.zgruppedetail': 'odoo_id'}
    _description = 'GetResponse Campaign (List)'

    backend_id = fields.Many2one(comodel_name='getresponse.backend', string='GetResponse Backend',
                                 required=True, ondelete='restrict')

    # HINT: If we delete a FRST group (zGruppeDetail) in odoo or FRST we do not want the GetResponse campaing to be
    #       deleted to. Instead one must first delete the GetResponseCampaign and then delete the FRST group!
    odoo_id = fields.Many2one(comodel_name='frst.zgruppedetail',
                              string='Fundraising Studio Group',
                              required=True, ondelete='restrict')
    getresponse_id = fields.Char(string='GetResponse Campaing ID', readonly=True)
```

You may also add the inverse fields on the related odoo model. In this case it would be ```frst.zgruppedetail```

Now we can create an ```adapter``` for the the  getresponse.frst.zgruppedetail model.

