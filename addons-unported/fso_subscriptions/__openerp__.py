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
    'name': "FS-Online fso_subscriptions",
    'summary': """FS-Online Subscription Management""",
    'description': """

Create and manage different kind of subscriptions:
  - E-Mail Subscriptions (e.g.: Newsletter- or Mailing-Groups)
  - Online Petitions (e.g.: Unterschriftenlisten)
  - Mobile Subscriptions (e.g.: SMS-Channels or WhatsApp)

This is done by expanding the models "mail.mass_mailing.list" and "mail.mass_mailing.contact".
These Models can be directly used by the mass mailing addon. 
Therefore it is more convenient to expand them than to create new ones ;)

Planned Features
----------------
  - Set the "type" of a mail.mass_mailing.list (called subscription list from now on)
    - Special types "one-shots/single-use-only" for subscription lists
      Those are used for MassMailings created in Fundraising Studio
  - Extended approval functions for list contacts
  - Adds all "Fundraising Studio Print-Field" fields to the list contact model
  - Adds common Partner fields to the list contact model
  - Controllers and Forms to subscribe and unsubscribe from lists
  - Provide Basic list contact statistics and informations (e.g. by menu buttons and group-by filters)
  - Set "Subscription Goals" and show how much is currently reached by a widget
  - Add html elements to provide "live" info about the subscription on the webpages
    - Live Ticker for Subscriptions
    - Live Ticker of last Subscribers
  - Invite others to subscribe
    - by email
    - publish on facebook

Features needed but solved by other addons:
  - Allow to "Approve" list contacts (e-mail double-opt-in)
  - Force the linking or creation of a partner for subscription list contacts (mail.mass_mailing.contact)
  - Follow-Up E-Mails on Subscriptions (Must be done by a Workflow right now but will be available by a new FRST addon)


    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        'fso_mass_mail',
        'fso_print_fields',
        'fso_forms',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/mail_mass_mailing_contact.xml',
        'views/mail_mass_mailing_list.xml',
        'views/templates.xml',
    ],
}
