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
    'name': "FS-Online fso_frst_groups_frst_cds",
    'summary': """FS-Online Fundrasing Studio Group System CDS extension""",
    'description': """
FS-Online Fundraising Studio Group System CDS Link.
Will add a relation between frst.zgruppedetail and frst.zverzeichnis

The use case for setting a CDS list (file) on a FRST Group (zGruppeDetail) is to use this as a hint for any
Fundraising Studio "Aktion" that may be created because a FRST Group is assigned (e.g.: Personemailgruppe) or changed
(e.g.: Status changed to 'confirmed' or 'OptOut')

This is part of the "customization" project with it's goal to solve more customer requirements without coding but with
settings in the program by our stuff or even the customer itself.

    """,
    'author': "Datadialog - Michael Karrer, Martin Kaip",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'fso_frst_groups',
        'fso_frst_cds',
    ],
    'data': [
        'views/frst_zgruppedetail.xml',
        'views/frst_personemailgruppe.xml',
        'views/frst_persongruppe.xml',
    ],
}
