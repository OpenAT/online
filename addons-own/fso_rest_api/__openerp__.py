# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
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
    'name': "FS-Online fso_rest_api",
    'summary': """FS-Online Rest API for Fundraising Studio""",
    'description': """
Create an openapi integration for the Fundraising Studio models and methods.

Includes a documentation based on restructured text and Sphinx

    """,
    'author': "Datadialog - Michael Karrer, Martin Kaip",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.2.0',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'openapi_metrics',
        'openapi_swagger_gui',
        'fsonline',
    ],
    'data': [
        'data/frst_api_user.xml',
        'data/frst_rest_api.xml',
        'data/res_partner.xml',
    ],
}
