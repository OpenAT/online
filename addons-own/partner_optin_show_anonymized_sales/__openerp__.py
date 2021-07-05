# -*- coding: utf-8 -*-
##############################################################################
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
    'name': "Partner optin_show_anoym_sales",
    'version': "1.0",
    'category': "Uncategorized",
    'summary': "Partner Opt-In Show Anonymized Sales",
    'description': """
Boolean field 'optin_show_anoym_sales' to store the agreement of the partner to display sales in anonymized forms 
e.g. in streams, on social media or on last-donation widgets
    """,
    'author': "Datadialog, Michael Karrer",
    'website': "http://www.datadialog.net",
    'depends': ['base'],
    'data': [
        'views/res_partner.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
