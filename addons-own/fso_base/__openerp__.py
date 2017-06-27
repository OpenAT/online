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
    'name': "FS-Online fso_base",
    'summary': """FS-Online common fields, addons, libs and tools""",
    'description': """

FS-Online fso_base
==================
REPLACES: 
- base_config
- base_mod (add instance port to res.company)
- base_tools (image.py)

Module tasks:
-------------
- Install all basic addons for an FS-Online instance
  - Use e-mail as the login
  - Use firstname and lastname for res.partner and use "firstname lastname" as order for name field
  - Use selection list for res.partner gender
- Add fields to res.company (fso_instance_id, fso_instance_port)
- Add fields to res.partner (title_web, birthdate_web, legal_terms_web, ...)
- Add fields to product.template (fs_product_type)
- Create all basic Fundrasing Studio related models
  - fs.group (Fundraising Studio Groups)
- Set defaults for all users (e.g.: timezone for the users)
- Set sale order policy to manual
- Set purchase order invoice_method to picking
- Set res company timesheet_range to month
- CSS adjustments for the odoo backend
- CSS adjustments for the chatter addon


TODO (must be done manually right now):
- Set language, country and timezone for the admin users
- Auto setup account chart for AT and taxes
- Auto setup real time warehouse transactions (accounts and setting)

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'version': '0.2',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        # Default odoo addons
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
        # Default Third Party Addons
        'dbfilter_from_header',
        'disable_openerp_online',
        'base_location',
        'base_location_geonames_import',
        'web_export_view',
        'report_custom_filename',
        'partner_contact_gender',
        # Default Own Addons
        'mail_follower_control',
        'mail_global_bcc',
        'partner_firstname_lastname',
        'partner_fullhierarchy',
        'auth_doubleoptin',
        'auth_partner',
        'web_logout_with_kwargs',
        'website_crm_extended',
        'website_blog_layouts',
    ],
    'data': [
        'data/setup.xml',
        'data/project_task_stages.xml',
        'security/fs_groups_security.xml',
        'security/ir.model.access.csv',
        'views/fsonline_menu.xml',
        'views/templates_backend_css.xml',
        'views/res_company.xml',
        'views/fs_groups.xml',
    ],
}
