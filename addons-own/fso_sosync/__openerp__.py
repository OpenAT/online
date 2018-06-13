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
The partner merge is also incuded in this addon!
Please check and extend partner_merge.py for new models if needed!

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
        #'crm',
        'fsonline',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/sosync_job.xml',
        'views/sosync_job_wizard.xml',
        'views/sosync_job_queue.xml',
        'views/sosync_job_queue_wizard.xml',
        'views/fsonline_menu.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/templates_backend_css.xml',
        'views/account_fiscalyear.xml',
        'data/actions.xml',
        'data/scheduled_actions.xml',
        'data/user_sosync.xml',
        'data/actions_on_update_install.xml',
    ],
    'qweb': [
        "static/src/xml/base.xml",
    ],
}
