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
    'name': "FS-Online fso_frst_groups",
    'summary': """FS-Online Fundrasing Studio Group System implementation""",
    'description': """
FS-Online Fundrasing Studio Group System implementation

TODO: There is some unicode error in addon fso_frst_groups on init - find and fix it!

    """,
    'author': "Datadialog - Michael Karrer, Martin Kaip",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'fso_frst_personemail',
        'fso_merge',
    ],
    'data': [
        'security/fs_groups_security.xml',
        'security/ir.model.access.csv',
        #
        'views/frst_persongruppe.xml',
        'views/frst_personemailgruppe.xml',
        #
        'views/frst_zgruppe.xml',
        'views/frst_zgruppedetail.xml',
        #
        'views/res_partner.xml',
        #
        'data/scheduled_actions.xml',
    ],
}
