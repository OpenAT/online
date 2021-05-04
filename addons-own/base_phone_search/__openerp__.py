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
    'name': "FS-Online base_phone_search",
    'summary': """Provides methods to search for phone numbers""",
    'description': """
    Provides the method search_phone_fuzzy() for res.partner.
    
    This method will search the 'phone' and 'mobile' fields of res.partner for the given phone number.
    
    It will by default ignore all non digit characters and will search 6 digits from right to left in the database.
    e.g.: '+43 (0)660 1234 - 567 ' will be converted to '7654321066034'
    Then it will check the results from the db with the python phonenumbers lib for equality 
    
    When we search for a phone number by self.env['res.partner'].search_phone_fuzzy('(0)660 12 34 567') we search for 
        1.) Search for partner where 'phone' or 'mobile' ends with '234567'
        2.) Use the phonenumbers Python Library to further narrow down the results
        3.) Return an record set with the found partner ids
    
    """,
    'author': "Datadialog",
    'website': "http://www.datadialog.net",
    'category': 'Uncategorized',
    'version': '1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'contacts',
    ],
    'data': [
        'run_on_install_update.xml',
    ],
}
