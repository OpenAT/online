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
    'name': "FS-Online fso_subscriptions_zgruppedetail",
    'summary': """FS-Online bind mailing_list to FRST zGruppeDetail""",
    'description': """
This addon is a helper until we completely switch from zGruppeDetail to mass.mailing_list and 
mass_mailing_list.contact for the management of mailing list subscriptions!

It creates and removes PersonEmailGruppe based on list contacts.

You could select the related zGruppeDetail in the mass mailing list! 
    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        'fso_frst_groups',
        'fso_subscriptions',
    ],
    'data': [
        'views/frst_zgruppedetail.xml',
        'views/mail_mass_mailing_list.xml',
        'views/mail_mass_mailing_contact.xml',
        'views/frst_personemailgruppe.xml',
    ],
}
