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
    'name': "FS-Online fso_sosync_partner_security",
    'summary': """Compute boolean fields to indicate user-security status of this partner for Fundraising Studio""",
    'description': """Adds computed boolean fields to the res.partner based on the user groups of the user of the 
partner.

This is to indicate Fundraising Studio to "do not merge or delete" any res.partner in Fundraising Studio that is 
linked to an FS-Online Administration- or System-User.
    
    """,
    'author': "Datadialog",
    'website': "http://www.datadialog.net",
    'category': 'Uncategorized',
    'version': '1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'fso_sosync',
    ],
    'data': [
        'data/run_on_install_update.xml',
    ],
}
