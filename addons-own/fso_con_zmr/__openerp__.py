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
    'name': "FS-Online fso_con_zmr",
    'summary': """FS-Online Austrian ZMR Connector""",
    'description': """
FS-Online fso_con_zmr
=====================
 
This addon determines the BPK number from FinanzOnline for partners and allows to submit donation reports.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'base',
        'fso_base',
        'fso_merge_partner',
    ],
    'data': [
        'security/group_res_partner_bpk_manager.xml',
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/res_partner_bpk.xml',
        'views/res_partner_donation_report.xml',
        'views/res_partner_donation_report_submissions.xml',
        'views/account_fiscalyear.xml',
        #'views/fsonline_menu.xml', # moved to fsonline
        #
        'data/install_update_actions.xml',
        'data/server_actions.xml',
        'data/scheduled_actions.xml',
    ],
}
