# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenSur.
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
    'name': 'website_forum_doc_private Documentation private',
    'category': 'Website',
    'website': '',
    'summary': 'website_forum_doc_private Documentation private access by Forum User Groups',
    'version': '1.00',
    'description': """
website_forum_doc_private
=========================
Add feature to have private document (TOC) entries, visible only for certain security groups of the related forum
        """,
    'author': 'Dadi',
    'depends': [
        'website_forum_private',
        'website_forum_doc'
    ],
    'data': [
        'data/access_rules.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
