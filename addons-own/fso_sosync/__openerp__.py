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
    'name': "FS-Online fso_sosync",
    'summary': """FS-Online sosync job tables""",
    'description': """

FS-Online fso_sosync
====================
- sosync.job
- sosync.job.queue

Additional Information
----------------------
!!! The partner merge is also incuded in this addon !!!
Please check and extend partner_merge.py for new models if needed!

You can add '_sync_job_priority' to values of create(values) or write(values) methods to set the job_priority field 
of a sync job! The value will be removed (popped) from values dict before the real 'create' or 'write' is run!

Priorities of 1.000.000 or higher will lead to instant sync job submission if addon 'fso_sosync_async' is installed!

It is also possible to set job_priority for a complete model! Just add '_sync_job_priority' to the class attributes.
Check addons-loaded/fso_sosync/models_sosync/email_template.py for an example.

New instance pillar options:
----------------------------
sosync_enabled: True
sosync_skipped_flows: SaleOrder,Partner,BPK|None

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        'fsonline',
    ],
    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        # Views and CSS
        'views/templates_backend_css.xml',
        'views/sosync_job_queue.xml',
        'views/sosync_job_queue_wizard.xml',
        # Deprecated Views
        'views/sosync_job.xml',
        'views/sosync_job_wizard.xml',
        # Data: User and Actions
        'data/actions.xml',
        'data/scheduled_actions.xml',
        'data/user_sosync.xml',
        # Extended Sosync-Model Views
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/account_fiscalyear.xml',
        'views/frst_personemail.xml',
        'views/frst_zgruppe.xml',
        'views/frst_zgruppedetail.xml',
        'views/frst_persongruppe.xml',
        'views/frst_personemailgruppe.xml',
        'views/res_partner_donation_report.xml',
        # Menu
        'views/fsonline_menu.xml',
    ],
    'qweb': [
        "static/src/xml/base.xml",
    ],
}
