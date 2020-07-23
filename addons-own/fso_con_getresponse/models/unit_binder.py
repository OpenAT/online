# -*- coding: utf-8 -*-
from openerp.addons.connector.connector import Binder
from .backend import getresponse


# HINT: This will register this Binder class in the main parent class 'ConnectorUnit' which has a slot for
#        a Binder class
#        a Mapper class
#        an Adapter class
#        a Syncronizer class
@getresponse
class GetResponseModelBinder(Binder):
    _model_name = [
        'getresponse.frst.zgruppedetail'
    ]

    # ATTENTION: This just uses the basic implementation of the binder - to make this work the fields names
    #            in the binding model must match the expected field names of the class 'Binder' OR tell the binder
    #            class the field names:
    _external_field = 'getresponse_id'
    _backend_field = 'backend_id'
    _openerp_field = 'odoo_id'
    _sync_date_field = 'sync_date'

    # INFO: we could do our own implementation of the binder: Just overwrite the expected method here like to_openerp()
