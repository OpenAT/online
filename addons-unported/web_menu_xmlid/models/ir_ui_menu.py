# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp.osv import osv
from openerp import api, tools
from openerp.tools import SUPERUSER_ID


class ir_ui_menu(osv.osv):
    _inherit = 'ir.ui.menu'

    @api.cr_uid_context
    @tools.ormcache_context(accepted_keys=('lang',))
    def load_menus(self, cr, uid, context=None):
        xmlid_obj = self.pool['ir.model.data']

        def add_xmlid_to_menu_root(mr={}):
            id = mr.get('id', False)
            if id:
                rec_id = xmlid_obj.search(cr, SUPERUSER_ID, [('model', '=', 'ir.ui.menu'), ('res_id', '=', id)], context=context)
                if rec_id:
                    rec = xmlid_obj.browse(cr, SUPERUSER_ID, rec_id, context=context)
                    if rec and rec.complete_name:
                        mr['xml_id'] = rec.complete_name
            children = mr.get('children', False)
            if children:
                for child in children:
                    add_xmlid_to_menu_root(mr=child)

        menu_root = super(ir_ui_menu, self).load_menus(cr=cr, uid=uid, context=context)

        add_xmlid_to_menu_root(mr=menu_root)

        # THIS COMMENTS/NOTES CAN BE REMOVED AFTER TESTING :)
        # test2 = xmlid_obj.search(cr, uid, [('model', '=', 'ir.ui.menu'), ('res_id', '=', '717')], context=context)
        # test3 = xmlid_obj.browse(cr, uid, test2, context=context)
        # inverse_test = xmlid_obj.get_object_reference(cr, uid, 'fso_base', test3.name)
        # inverse_test2 = xmlid_obj.xmlid_to_object(cr, uid, test3.complete_name)

        return menu_root
