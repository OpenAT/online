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
    'name': "base_config",
    'summary': """Setup and Configuration Tool""",
    'description': """

Setup and configuration tool
============================

This module makes it easy to setup and configure a new database for odoo. It ensures that all setups are basically
the same and makes it easy to include new default addons and settings.



Module tasks:
-------------

- Install all common addons
- Overwrite some of the backend CSS (forms-fullwidth, chatter, colors)
- Create a new configuration menu for addons-own and addons-thirdparty linked in addons-loaded
- ToDo: Set default values for the admin user (timezone, technical features, language)
- Set/Create Project Stages (= Task Stages = Issue Stages)
- ToDo: Setup Real-Time Warehouse Transactions, Create needed Accounts and use them in the product categories
- ToDo: Set "Validate Timesheets every" to: Month
- ToDo: Auto-Create a standard working schedules for 38,7 h and 40,0 h per week
- Set default values in "settings > configuration" (groups and modules) as far as possible


You still need to do some things by Hand after installing this module:
----------------------------------------------------------------------

- Set Chart of Accounts and Tax (Wizzard will pop up while installing)
- Set Defaults for Admin-User and Template User (Timezone, Signature, ...)
- Set the Timesheet Validation to "Month"
- Create Standard Work Shedules and link them to employees
- Create The Accounts for real-time warehouse moves and link them in the product-groups (maybe obsolete in v8.0?)

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.2',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        # Odoo default addons
        'base', 'crm', 'mail',
        'account_voucher', 'project', 'note', 'project_issue', 'account_accountant', 'survey', 'sale','stock',
        'purchase', 'hr', 'hr_timesheet_sheet', 'hr_recruitment', 'hr_holidays', 'hr_expense', 'hr_evaluation',
        'calendar', 'contacts', 'gamification', 'im_livechat', 'lunch',
        'mass_mailing', 'project_timesheet', 'sale_service', 'account_analytic_analysis', 'delivery', 'warning',
        'sale_stock', 'sale_margin', 'analytic_user_function', 'crm_claim', 'crm_helpdesk','stock_dropshipping',
        'stock_landed_costs', 'procurement_jit', 'stock_picking_wave', 'project_issue_sheet', 'account_asset',
        'account_followup', 'product_email_template', 'account_payment', 'hr_contract', 'document',
        'website', 'website_blog', 'website_event', 'website_forum', 'website_sale',
        'website_certification', 'website_crm', 'website_crm_partner_assign', 'website_customer', 'website_event_sale',
        'website_event_track', 'website_forum_doc', 'website_gengo', 'website_google_map', 'website_hr',
        'website_hr_recruitment', 'website_mail', 'website_mail_group', 'website_membership', 'website_partner',
        'website_payment', 'website_project', 'website_quote', 'website_report', 'website_sale',
        'website_sale_delivery', 'website_twitter', 'base_iban',
        # Forced Third Party Addons
        'base_location',
        'base_location_geonames_import',
        'dbfilter_from_header',
        'disable_openerp_online',
        'web_export_view',
        'report_custom_filename',
        'partner_contact_gender',
        # Forced Own Addons
        'mail_follower_control',
        'mail_global_bcc',
        'partner_firstname_lastname',
        'partner_fullhierarchy',
        'auth_doubleoptin',
        'web_logout_with_kwargs',
        'website_sale_donate',
        'website_crm_extended',
        'website_blog_layouts',
        'payment_frst',
        'payment_ogonedadi',
        'payment_postfinance',
        'fs_groups',
        'auth_partner',
        'auth_partner_form',
    ],
    'data': [
        'data/data_project.xml',
        'data/data_setup_css.xml',
        'data/data_sosync_user.xml',
        'security/ir.model.access.csv',
        'views/res_config.xml',
    ],
}
