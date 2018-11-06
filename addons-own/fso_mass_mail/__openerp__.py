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
  - Change FRST print fields to odoo mako expressions
  - Convert links in the email to tracked links
  - Integrate link tracking statistics to mass mail views
  - Option to stop sending queue
  - Option to restart sending queue
  - New Menu for FS-Online
    Channels
      - Mass Mailing
        - Campaigns
        - Mass Mails
        - Mailing Lists
        - Lists Contacts
        - Sending Queue
      - E-Mail
        - E-Mails
        - Templates (with default fso filter)
        - Statistics
  - 

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
        'fso_website_email',                # New E-Mail editor and custom routes
        #'mass_mailing_sending_queue',       # Prepare massmailing e-mails in background by cron Job
        #'mail_connector_queue',             # Send E-Mails async by connector queue
        #'mail_tracking_mass_mailing',       # Status, Score, AVOID RESEND for mass mailings after e.g. domain change!
        #'mass_mailing_statistic_extra',     # from, to and subject is available in the statistics table
        'utm',
        'link_tracker',
    ],
    'data': [
        'views/views.xml',
        #'views/email_editor.xml',
    ],
}
