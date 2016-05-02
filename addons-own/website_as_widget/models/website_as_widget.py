# -*- coding: utf-'8' "-*-"
__author__ = 'mkarrer'

from openerp.osv import osv, orm, fields


class website_settings(osv.Model):
    _inherit = 'website'
    _columns = {
        # Checkout Pages Headers
        'global_redirect_url': fields.char(string='Global redirect URL',
            help='Used if not called with aswidget=True and not from a configuration URL',
                                           translate=True),
        'global_configuration_urls': fields.char(string='Configuration URLS separated by ;',
            help='Any URL other than a configuration URL or localhost will redirect to the global_redirect_url if set'),
    }


class website_config_settings(osv.osv_memory):
    _inherit = 'website.config.settings'

    _columns = {
        'global_redirect_url': fields.related('website_id', 'global_redirect_url',
                                              type="char",
                                              string='Global redirect URL',
            help='Used if not called with aswidget=True and not from a configuration URL',
                                              translate=True),
        'global_configuration_urls': fields.related('website_id', 'global_configuration_urls', type="char",
            string='Configuration URLS separated by ;',
            help='Any URL other than a configuration URL or localhost will redirect to the global_redirect_url if set'),
    }
