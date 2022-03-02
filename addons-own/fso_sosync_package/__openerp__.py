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
    'name': "FS-Online fso_sosync_package",
    'summary': """FS-Online sosync meta package for default addons""",
    'description': """
This package is a meta package, installing all default sosnyc packages that should be
installed, if an instance gets activated for sosync.

Only depend on packages that should be installed by default on ALL instances.

Do NOT depend on specific sosync packages that are only applicable to some instances.
    """,
    'author': "Datadialog",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        # Only depend on sosync modules that work for ALL instances
        # do NOT add sepcific sosync modules (for example, GR, facebook, etc.)
        # 'fso_sosync', # Is a dependency of other modules anyway
        'fso_sosync_payment_consale',
        'fso_sosync_fso_frst_xbankverbindung',
        'fso_sosync_fso_frst_xbankverbindung_payment',
        'fso_sosync_product',
        'fso_sosync_survey',
    ],
    'data': [
     ],
}
