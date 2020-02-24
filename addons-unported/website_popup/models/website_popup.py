# -*- coding: utf-'8' "-*-"
__author__ = 'mkarrer'

from openerp.osv import osv, orm, fields


class website_popup(osv.Model):
    _inherit = 'website'
    _columns = {
        # Global Fields for Snippet Dropping
        'website_popup': fields.html(string='PopUpBox Content', translate=True),
        'website_popup_cancel_button': fields.char(string='PopUpBox Button Text', translate=True),
        'website_popup_start': fields.datetime(string='PopUpBox Start Date'),
        'website_popup_end': fields.datetime(string='PopUpBox End Date'),
    }
    _defaults = {
        'website_popup_cancel_button': 'Hide me permanently!',
    }

class website_config_settings(osv.osv_memory):
    _inherit = 'website.config.settings'

    _columns = {
        'website_popup_cancel_button': fields.related('website_id', 'website_popup_cancel_button', type="char",
                                                      string='PopUpBox Button Text', translate=True),
        'website_popup_start': fields.related('website_id', 'website_popup_start', type="datetime",
                                              string='PopUpBox Start Date'),
        'website_popup_end': fields.related('website_id', 'website_popup_end', type="datetime",
                                            string='PopUpBox End Date'),
    }
