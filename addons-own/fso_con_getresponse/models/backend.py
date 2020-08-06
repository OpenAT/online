# -*- coding: utf-8 -*-
from openerp import fields, models, api
import openerp.addons.connector.backend as backend

# Global variables to make the backend globally available
getresponse = backend.Backend('getresponse')
""" Generic GetResponse Backend """

getresponse_v3 = backend.Backend(parent=getresponse, version='v3')
""" GetResponse Backend for API version 3.0 """
