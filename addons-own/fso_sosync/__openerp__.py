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

New instance pillar options:
----------------------------
sosync_enabled: True
sosync_skipped_flows: SaleOrder,Partner,BPK|None

host_sosyncgw: sosync1
host_sosyncdb: sosync1

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
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/sosync_job.xml',
        'views/sosync_job_queue.xml',
        #'views/fsonline_menu.xml',
    ],
}
