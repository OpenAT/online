# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import openerp.addons.connector.backend as backend


getresponse = backend.Backend('getresponse')
getresponse_v3 = backend.Backend(parent=getresponse, version='v3')
