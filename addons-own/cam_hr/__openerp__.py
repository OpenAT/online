# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Human Resources by Camadeus GmbH',
    'category': 'Custom', 
    'version': '1.0',
    'description': """
Human Resource Adaptions
===========================
* Easy and intuitive menu structure
* Public holiday management
* Customizations for german speaking countries
    """,
    'author': 'camadeus GmbH',
    'website': 'http://www.camadeus.at',
    'depends': ['cam_hr_overtime','project_timesheet'],
    'data': [
             'security/ir.model.access.csv',
             'security/cam_hr_security.xml',             
             'wizard/import_feiertage_view.xml',
             'hr_data.xml',
             'hr_view.xml',
             'hr_cron.xml',   
        ],
    'css' : [
             
    ],    
    'installable': True,
    'sequence': 150,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
