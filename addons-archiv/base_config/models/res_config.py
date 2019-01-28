# -*- coding: utf-8 -*-
##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
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

import time
import datetime
from dateutil.relativedelta import relativedelta

import openerp
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
from openerp.osv import fields, osv


class base_config_settings(osv.osv_memory):
    _name = "base_config.settings"
    _inherit = 'res.config.settings'
    _columns = {
        # Working Third Party Addons
        'module_base_field_serialized': fields.boolean('base_field_serialized -- Adds fields of type serialized to odoo v8',
                                                       help='Could be needed by older modules - and Aeroo Reports!'
                                                            '\n Installs Module: base_field_serialized'),
        'module_base_location': fields.boolean('base_location -- City/Zip auto complete',
                                               help='Makes it easier to fill all the Data for Zip, City and State'
                                                    '\n Installs Module: base_location'),
        'module_base_location_geonames_import': fields.boolean('base_location_geonames_import -- Donwload City, Zip, State Information',
                                                               help='You could download / update City, Zip and State information!'
                                                                    '\n Installs Module: base_location_geonames_import'),
        'module_dbfilter_from_header': fields.boolean('dbfilter_from_header -- This addon lets you pass a dbfilter as a HTTP header.',
                                                      help='This addon lets you pass a dbfilter as a HTTP header.'
                                                           '\n Installs Module: dbfilter_from_header'),
        'module_disable_openerp_online': fields.boolean('disable_openerp_online -- Disable all Spy from OpenERP SA',
                                                        help='Removes Warning, Online Help and Online Apps'
                                                             '\n Installs Module: disable_openerp_online'),
        'module_mass_editing': fields.boolean('mass_editing -- Mass Editing for any field (set and unset possible)',
                                              help='You could create Mass-Editing-Actions for any modell.field in odoo!'
                                                   '\n Installs Module: mass_editing'),
        'module_web_export_view': fields.boolean('web_export_view -- Export any Tree-View as Excel Sheet',
                                                 help='This tool makes the export of tree views much easier since it exports the view as seen on screen!'
                                                      '\n Installs Module: web_export_view'),
        'module_web_m2x_options': fields.boolean('web_m2x_options -- More xml view widget options for many2x fields',
                                                 help='Adds options to hide create or create and edit for many2x fields!'
                                                      '\n Installs Module: web_m2x_options'),
        'module_website_menu_by_user_status': fields.boolean('website_menu_by_user_status -- Show Webpages depending on the login status',
                                                 help='Adds options to hide show webpages in Settings - Website - Pages!'
                                                      '\n Installs Module: website_menu_by_user_status'),
        'module_website_blog_mgmt': fields.boolean('website_blog_mgmt -- Adds a publish date to blog posts',
                                                 help='The new publish date field controlls the order and the start date of the blog post!'
                                                      '\n Installs Module: website_blog_mgmt'),
        'module_website_sale_collapse_categories': fields.boolean('website_sale_collapse_categories -- collapseabel webshop categories',
                                                 help='Adds options to make webshop categories collapsible by java script!'
                                                      '\n Installs Module: website_sale_collapse_categories'),
        'module_web_dialog_size': fields.boolean('web_dialog_size -- Full width for dialog boxes (nest to close box)',
                                                 help='Adds button to make dialog popup boxes fill screen width!'
                                                      '\n Installs Module: web_dialog_size'),
        'module_web_graph_improved': fields.boolean('web_graph_improved -- compare to measures in graph view',
                                                 help='compare to measures in graph view!'
                                                      '\n Installs Module: web_graph_improved'),
        'module_web_widget_many2many_tags_multi_selection': fields.boolean('web_widget_many2many_tags_multi_selection -- select multible many2many results',
                                                 help='select multiple results in search-more of many2many fields'
                                                      '\n Installs Module: many2many_tags_multi_selection'),
        'module_website_files': fields.boolean('website_files -- Add a Files tab to the image website dialogue',
                                                 help='Upluad Files and insert Links for Download'
                                                      '\n Installs Module: module_website_files'),
        'module_mail_delete_access_link': fields.boolean('mail_delete_access_link -- Delete Access-Document Link from odoo emails'),
        'module_mail_delete_sent_by_footer': fields.boolean('mail_delete_sent_by_footer -- Remove send by odoo from odoo emails'),
        'module_web_advanced_search_x2x': fields.boolean('web_advanced_search_x2x -- Better search for x2many fields'),
        'module_web_translate_dialog': fields.boolean('web_translate_dialog -- Easier Translation Dialog for odoo modules'),
        'module_website_no_crawler': fields.boolean('website_no_crawler -- Write new Robots.txt to disallow site indexing while developping'),
        'module_website_redirect': fields.boolean('website_redirect -- Create redirects in the odoo backend'),
        'module_mail_sent': fields.boolean('mail_sent -- Add a SENT Menu to odoo'),
        'module_mail_outgoing': fields.boolean('mail_outgoing -- Outgoing E-Mail overview for admins'),
        'module_mail_fix_553': fields.boolean('mail_fix_553 -- change Domain of FROM field for outgoing mails'),
        'module_inactive_session_timeout': fields.boolean('inactive_session_timeout -- Remove all inactive session after a given time'),
        'module_website_event_register_free': fields.boolean('website_event_register_free -- prevents sales order and shop payment on cost free event tickets'),
        'module_report_custom_filename': fields.boolean('report_custom_filename -- Better Filename Setting for reports through download_filename field'),
        'module_report_qweb_element_page_visibility': fields.boolean('report_qweb_element_page_visibility -- Add extra classes for qweb reports'),
        'module_website_sale_autopay': fields.boolean('website_sale_autopay -- Auto create and validate invoice from webshop order'),
        'module_partner_firstname': fields.boolean('partner_firstname -- Add a firstname and lastname field to parnters and make name a function field'),
        'module_partner_contact_gender': fields.boolean('partner_contact_gender -- Add a gender selection field to parnters'),
        # o8r35
        'module_website_blog_private': fields.boolean(
            'website_blog_private -- Set odoo groups for blog access'),
        'module_website_forum_private': fields.boolean(
            'website_forum_private -- Set odoo groups for forum access'),
        'module_website_cookie_notice': fields.boolean(
            'website_cookie_notice -- Add a cooky notice to the webpage'),
        'module_website_legal_page': fields.boolean(
            'website_legal_page -- Add a legal page to the webpage'),
        'module_website_seo_redirection': fields.boolean(
            'website_seo_redirection -- Replace or redirect webpage URLS'),
        'module_website_snippet_anchor': fields.boolean(
            'website_snippet_anchor -- Add Anchors to page Elements'),
        'module_website_snippet_contact_form': fields.boolean(
            'website_snippet_contact_form -- Drag and Drop Contact Form'),
        'module_website_snippet_image_gallery': fields.boolean(
            'website_snippet_image_gallery -- Simple Image Wall'),
        'module_web_groupby_expand': fields.boolean(
            'web_groupby_expand -- Expand all grouped nodes at once in backend'),

        # Addons Own
        'module_website_crm_extended': fields.boolean('website_crm_extended -- Default sales group for lead from contact formular',
                                                       help='Adds default sales group for lead creation from website contact formular so that an automatic e-mail can be send'
                                                            '\n Installs Module: website_crm_extended'),
        'module_payment_frst': fields.boolean('payment_frst -- FRST Payment Provider (SEPA - Bankeinzug)',
                                              help='Payment Provider for IBAN and BIC (Bankeinzug)'
                                                   '\n Installs Module: payment_frst'),
        'module_website_sale_donate': fields.boolean('website_sale_donate -- Shop Extensions for Online Fundraising',
                                                     help='Add arbitrary price, hide amount and other features to website_sale'
                                                          '\n Installs Module: website_sale_donate'),
        'module_project_basic_extensions': fields.boolean('project_basic_extensions -- Basic Project Extensions',
                                                          help='A lot of small tweaks to project, tasks and issues'
                                                          '\n Installs Module: website_sale_donate'),
        'module_website_highlight_code': fields.boolean('website_highlight_code -- Forum Code Highlighting',
                                                      help='Includes highlight.js and add new addons to ckeditor of forum'
                                                           '\n Installs Module: website_sale_catdesc'),
        'module_mail_follower_control': fields.boolean('mail_follower_control -- Mail Follower Control',
                                                      help='Control the Followers of E-Mails'
                                                           '\n Installs Module: mail_follower_control'),
        'module_website_sale_payment_fix': fields.boolean('website_sale_payment_fix -- Payment Transaction fix for the Webshop',
                                                      help='Resets the Webshop after Payment Button is pressed for some PP'
                                                           '\n Installs Module: website_sale_payment_fix'),
        'module_payment_ogonedadi': fields.boolean('payment_ogonedadi -- Payment Provider Ogone extended by Dadi',
                                                      help='Extended Ogone Payment Provider that will work with multible answers from ogone even if odoo web session is lost.'
                                                           '\n Installs Module: payment_ogonedadi'),
        'module_payment_postfinance': fields.boolean('payment_postfinance -- Payment Provider ESR Postfinance for CH',
                                                      help='ESR Payment Provider'
                                                           '\n Installs Module: payment_postfinance'),
        'module_mail_global_bcc': fields.boolean('mail_global_bcc -- send all outgoing emails to a email address defined in mail.outgoing.global.bcc',
                                                      help='send all outgoing emails to a email address defined in mail.outgoing.global.bcc in the ir.config_parameter settings'
                                                           '\n Installs Module: mail_global_bcc'),
        'module_website_sale_categories': fields.boolean('website_sale_categories -- more controll for display of public shop categories',
                                                         help='hide category, start navigation from this category, category descriptions'
                                                         '\n Installs Module: website_sale_categories'),
        'module_website_blog_layouts': fields.boolean('website_blog_layouts -- show images in blog post list pages',
                                                         help='Enable Show Image at Blog Post List Page'
                                                         '\n Installs Module: website_blog_layouts'),
        'module_website_sale_login': fields.boolean('website_sale_login -- better login pages and user detection by e-mail',
                                                         help='This addon depends on auth_signup for signup or account creation and can be used with auth_doubleoptin also'
                                                         '\n Installs Module: website_sale_login'),
        'module_auth_doubleoptin': fields.boolean('auth_doubleoptin -- for account signup and newsletter subscription verification',
                                                         help='for account signup and newsletter subscription verification'
                                                         '\n Installs Module: auth_doubleoptin'),
        'module_partner_fullhierarchy': fields.boolean('partner_fullhierarchy -- allow parents and children for all partners',
                                                         help='allow parents and children for all partners and not just companies!'),
        'module_calendar_log': fields.boolean('calendar_log -- extend the calendar to use it as a log for meeting minutes',
                                                         help='calendar as log for meeting minutes'),
        'module_calendar_log_project': fields.boolean('calendar_log_project -- extend the calendar to use it as a log for work logs',
                                                         help='use the calendar as a simple work log. log work hours to projects or tasks'),
        'module_website_tools': fields.boolean('website_tools -- Basic JS libs and css fixes',
                                                         help='Library to avoid double loading of java libs and css'),
        'module_mail_delete_access_link_portal': fields.boolean('mail_delete_access_link_portal -- Delete Access-Document Link from odoo portal emails (see mail_delete_access_link too)'),
        'module_partner_firstname_lastname': fields.boolean('partner_firstname_lastname -- Install partner_firstname and change order to firstname, lastname'),
        'module_fs_groups': fields.boolean('fs_groups -- Fundraising Studio Groups for product.product'),
        'module_website_base_setup': fields.boolean('website_base_setup -- Website Basic Settings for all customers, robots.txt ...'),


        # Bugy Third Party Addons. Do not link or install (still there as reference)
        'module_web_ckeditor4': fields.boolean('web_ckeditor4 -- DEPRECATED! CKeditor4 for any html/text field in the odoo backend!',
                                               help='This is for Version 7 of odoo and is only there for development purposes.'
                                                    '\n Installs Module: web_ckeditor4'),
        'module_web_tree_many2one_clickable': fields.boolean('web_tree_many2one_clickable -- Make many2one fields clickabe in tree views',
                                                             help='You can set a global config option to use this in any tree view - web_tree_many2one_clickable.default True'
                                                                  '\n Installs Module: web_tree_many2one_clickable'),
        'module_help_online': fields.boolean('help_online -- Create a help page for any odoo backend view',
                                             help='This makes it easy to create an inline help for the users of odoo'
                                                  '\n Installs Module: help_online'),
        'module_web_recipients_uncheck': fields.boolean('web_recipients_uncheck Uncheck default receipients of chatter (e-mail)',
                                                        help='Normaly you can not untick receipients of chatter messages - this makes it possible!'
                                                             '\n Installs Module: web_recipients_uncheck'),
        'module_email_cc_bcc': fields.boolean('email_cc_bcc -- Add bcc and cc fields to chatter e-mails',
                                              help='Add bcc and cc fields to chatter e-mai!'
                                                   '\n Installs Module: email_cc_bcc'),
        'module_web_filter_tabs': fields.boolean('web_filter_tabs -- Save Searches as Tabs',
                                                 help='Save Searches as Tabs'
                                                      '\n Installs Module: web_filter_tabs'),
        'module_web_group_expand': fields.boolean('web_group_expand -- Unfold or Fold groups in tree views',
                                                  help='Unfold or Fold groups in tree views!'
                                                       '\n Installs Module: web_group_expand'),
        'module_project_code': fields.boolean('project_code -- Add a Code to Projects',
                                              help='Add a code to project.project and make it visible and searchable!'
                                                   '\n Installs Module: project_code'),
        'module_website_search': fields.boolean('website_search -- Global search box for the webpage',
                                                help='Global search box for the webpage'
                                                     '\n Installs Module: website_search'),
        'module_website_lang_flags': fields.boolean('website_lang_flags -- Language Flags for website lang selector',
                                                    help='Language Flags instead of just text for lang selector on website'
                                                         '\n Installs Module: website_lang_flags'),

    }
