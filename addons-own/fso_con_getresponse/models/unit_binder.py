# -*- coding: utf-8 -*-
from openerp import models
from openerp.addons.connector.connector import Binder
from .backend import getresponse

import json


# HINT: This will register this Binder class in the main parent class 'ConnectorUnit' which has a slot for
#        a Binder class
#        a Mapper class
#        an Adapter class
#        a Syncronizer class
@getresponse
class GetResponseModelBinder(Binder):
    _model_name = [
        'getresponse.frst.zgruppedetail'            # Getresponse Campaigns
    ]

    # ATTENTION: This just uses the basic implementation of the binder - to make this work the fields names
    #            in the binding model must match the expected field names of the class 'Binder' OR tell the binder
    #            class the field names:
    _external_field = 'getresponse_id'
    _backend_field = 'backend_id'
    _openerp_field = 'odoo_id'
    _sync_date_field = 'sync_date'

    # INFO: we could do our own implementation of the binder: Just overwrite the expected method here like to_openerp()
    
    def bind(self, external_id, binding_id, sync_data=None):
        # Call the original bind() method to write the sync_date field
        res = super(GetResponseModelBinder, self).bind(external_id=external_id, binding_id=binding_id)

        # Make sure binding_id is an odoo record
        if not isinstance(binding_id, models.BaseModel):
            binding_id = self.model.browse(binding_id)

        # Update 'sync_data' field of the binding record for comparison (concurrent write detection) at the next sync
        last_sync_data_json = json.dumps(sync_data, ensure_ascii=False).encode('utf8')
        binding_id.with_context(connector_no_export=True).write({'sync_data': last_sync_data_json})

        return res

