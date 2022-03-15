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
    'name': "FS-Online fso_sosync_fso_crm_facebook_leads",
    'summary': """Enable CRM Leads synchronization via Sosync""",
    'description': """
FS-Online fso_sosync_fso_crm_facebook_leads
===========================================
Specifies sosync tracked fields for model crm.lead

    """,
    'author': "Datadialog",
    'website': "http://www.datadialog.net",
    'category': 'Uncategorized',
    'version': '0.5',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'fso_sosync_base',
        'fso_crm_facebook_leads',
    ],
    'data': [
    ],
}
