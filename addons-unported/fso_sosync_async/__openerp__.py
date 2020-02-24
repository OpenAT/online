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
    'name': "FS-Online fso_sosync_async",
    'summary': """Immediate async sosync_job submission for high priority jobs""",
    'description': """

FS-Online fso_sosync_async
==========================
Submits VERY high priority (>= 1.000.000) sync jobs by connector async queue instead of the cron job.

The cron job is still there and activated for normal priority jobs and as a fallback! 


    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        #'connector',
        'connector_job_no_user',
        'fso_sosync',
    ],
    'data': [
        'run_on_install_update.xml',
    ],
    #'post_init_hook': 'post_init_hook',
    #'uninstall_hook': 'uninstall_hook',
}
