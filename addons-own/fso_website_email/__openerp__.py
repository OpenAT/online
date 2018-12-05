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
    'name': "FS-Online fso_website_email",
    'summary': """Website E-Mail Editor Extensions""",
    'description': """

FS-Online fso_website_email
===========================

!!! Make absolutely sure the users creating, editing AND sending E-Mails are set to the correct language DE_DE !!!

HINT: It is not tested yet if the language of the res.partner would also have any effect on mail sending !!!

ATTENTION: The langauge settings of odoo, the website as well as the user that edits and sends e-mails is
           VERY IMPORTANT!!! Otherwise only e.g.: DE_DE is changed but the E-Mail will be send in EN_US !
           Make absolutely sure the users creating, editing AND sending E-Mails are set to the correct language DE_DE!

WYSIWYG Editor for FRST E-Mail (Templates) to generate email body html for FRST Multimailer (fso_email_html_parsed).
It is also the base to use odoo mass Mailing for FRST E-Mails.

If comes with new routes to be used by FRST or as a standalone editor without the odoo GUI:

  - /fso/email/select
  
  - /fso/email/preview?template_id=
  - /fso/email/edit?template_id=
  - /fso/email/create?template_id=
  - /fso/email/delete?template_id=
    
  - /fso/email/version/create?template_id=
  - /fso/email/version/restore?template_id=
  
  - /fso/email/snippets  
  

This addon includes new example snippets and basic E-Mail templates as well as extensions to the java front end 
editor and it's tools like the href edit pop-up window.

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': [
        'website_mail',
        'fso_print_fields',
    ],
    'data': [
        'views/views.xml',
        #
        'views/email_editor.xml',
        'views/email_selection.xml',
        #
        'views/theme.xml',
        'views/snippets.xml',
        #
        'views/theme_default_snippets.xml',
        #
        'views/theme_dadi.xml',
        #
        'data/scheduled_actions.xml',
    ],
    'qweb': [
    ],
}
