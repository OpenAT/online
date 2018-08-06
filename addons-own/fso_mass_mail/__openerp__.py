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
    'name': "FS-Online fso_mass_mail",
    'summary': """FS-Online Mass Mailing System""",
    'description': """

Send Mass Mails (e.g.: Newsletters) with E-Mail Templates from fso_website_emails

Features
--------
  - Link (fso) email template to mass mailing
  - Open (fso) email template in edit mode from mass mailing
  - Update mass.mailing fields from email template
    - Change FRST print fields to mako expressions
  - Convert links in the email to tracked links
  - Include oca mass mailing queue addon (mass_mailing_sending_queue)
  - Option to stop sending queue
  - Option to restart sending queue
  - New Menu for FS-Online
    Channels
      - Mass Mailing
        - Campaigns
        - Mass Mails
        - Mailing Lists
        - ML Contacts
        - Sending Queue
      - E-Mail
        - E-Mails
        - Templates (with default fso filter)
        - Statistics



HINT: A change to the e-mail template will update all corresponding fields of the assigned mail.mass_mailing(s)
  mail.mass_mailing:
    - body_html
    - email_from
    - reply_to
    - name (Subject of E-Mail)

HINT: Body HTML of mass mailing will replace Fundrasing Studio Print Fields with odoo mako expressions

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        'mass_mailing',
        'fso_website_email',
        #'mass_mailing_sending_queue',
        'utm',
        'link_tracker',
    ],
    'data': [
        'views/views.xml',
        #'views/email_editor.xml',
    ],
}
