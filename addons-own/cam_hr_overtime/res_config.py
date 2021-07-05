# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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

from openerp.osv import fields, osv

class cam_hr_ovetime_config_settings(osv.osv_memory):
    _inherit = 'hr.config.settings'

    _columns = {
        'time_credit': fields.integer('Time Credit', required=True,
                                      help='Time credit in minutes when doing SignIn/SignOut'),
        'max_difference_day': fields.integer('Max difference per Day', required=True,
                                      help='Max difference per day in minutes. If difference is higher, it will raise a warning each sign in/sign out with the specific days. User wont be able to confirm the timesheet, if there are >1 days.\nThis check is only active if value > 0.'),
        'lunch_duration': fields.integer('Lunch Duration', help='Lunch duration in minutes (used for Lunch-button)'),
        'vacation_type_id': fields.many2one('hr.holidays.status', 'Holiday state of vacation', index=True),
        'illness_type_id': fields.many2one('hr.holidays.status', 'Holiday state of illness', index=True,),
        'zeitausgleich_type_id': fields.many2one('hr.holidays.status', 'Holiday state of Zeitausgleich', index=True, ),
        'homeoffice_type_id': fields.many2one('hr.holidays.status', 'Holiday state of Home-Office', index=True, ),
    }
    
    def get_default_overtime_values(self, cr, uid, fields, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return {
            'time_credit': user.company_id.time_credit,
            'max_difference_day': user.company_id.max_difference_day,
            'lunch_duration': user.company_id.lunch_duration,
            'vacation_type_id': user.company_id.vacation_type_id and user.company_id.vacation_type_id.id or False,   
            'illness_type_id': user.company_id.illness_type_id and user.company_id.illness_type_id.id or False,
            'zeitausgleich_type_id': user.company_id.zeitausgleich_type_id and user.company_id.zeitausgleich_type_id.id or False,
            'homeoffice_type_id': user.company_id.homeoffice_type_id and user.company_id.homeoffice_type_id.id or False,
        }

    def set_default_timesheet(self, cr, uid, ids, context=None):
        super(cam_hr_ovetime_config_settings, self).set_default_timesheet(cr, uid, ids, context)
        
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({
            'time_credit': config.time_credit,
            'max_difference_day': config.max_difference_day,
            'lunch_duration': config.lunch_duration,
            'vacation_type_id': config.vacation_type_id and config.vacation_type_id.id,
            'illness_type_id': config.illness_type_id and config.illness_type_id.id,
            'zeitausgleich_type_id': config.zeitausgleich_type_id and config.zeitausgleich_type_id.id,
            'homeoffice_type_id': config.homeoffice_type_id and config.homeoffice_type_id.id,
        })

cam_hr_ovetime_config_settings()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
