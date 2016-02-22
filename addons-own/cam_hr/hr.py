# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import config
from openerp import SUPERUSER_ID
from openerp import api
import time
                  

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    
    def get_parent_emp(self, cr, uid, context=None):
        id = self.search(cr,uid,[('user_id','=',uid)],limit=1)
        if id:
            return id[0]
        return False
    
    def get_default_product(self, cr, uid, context=None):
        m  = self.pool.get('ir.model.data')
        
        try:
            default_product = m.get_object(cr, uid, 'product', 'product_product_consultant')
            if default_product:
                return default_product.id
        except:
            pass
        
        return False
    
    def create(self, cr, uid, vals, context={}):
        res_id = super(hr_employee, self).create(cr, uid, vals, context)
        
        template_obj = self.pool.get('hr.holidays.template')
        
        template_id = template_obj.search(cr,uid,[('create_employees','=',True)],limit=1)
        
        if template_id:
            from openerp.addons.cam_hr.wizard.import_feiertage import wizard_feiertage
            wizard_obj = self.pool.get('wizard.import_feiertage')
            wizard_id = wizard_obj.create(cr,uid,{'template_id':template_id[0],'employee_ids':[(6,0,[res_id])]},context)
            wizard_feiertage.import_feiertage(wizard_obj,cr,uid,[wizard_id],context)
            
        return res_id 
            
        
    _defaults = {  
           'parent_id': get_parent_emp,
           'product_id': get_default_product
           }   
    
class hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    
    _order = 'date_from asc'

    _defaults = {
        'date_from': False,
    }

    @api.onchange('date_from')
    def _onchange_date_from(self):
        self.date_to = self.date_from
    
    #to maintain backward compatibility: create fake datetime. as we only use date widget
    def create(self, cr, uid, vals, context=None):
        date_from = vals.get('date_from',False)
        date_to = vals.get('date_to',False)
                
        if date_from and not date_to:
            vals['date_to'] = date_from
        
        type = context.get('leave_code',False)
        
        if not vals.get('name',False):
            if vals.get('employee_id',False):
                emp = self.pool.get('hr.employee').browse(cr, uid, vals.get('employee_id',False))
            else:
                emp = False
                
            if type=='vacation':
                vals['name'] = 'Urlaub: %s' % (emp and emp.name or 'Unknown')

            if type=='legal':
                vals['name'] = 'Feiertag: %s' % (emp and emp.name or 'Unknown')
            if type=='illness':
                vals['name'] = 'Krankenstand: %s' % (emp and emp.name or 'Unknown')
        
        vals = self.__addFakeDateTime(vals)
        res = super(hr_holidays, self).create(cr, uid, vals, context)
        return res 
    
    def write(self, cr, uid, ids, vals, context=None):
        vals = self.__addFakeDateTime(vals)
        res = super(hr_holidays, self).write(cr, uid, ids, vals, context)
        return res 
    
    
    def __addFakeDateTime(self,vals):
        date_from = vals.get('date_from',False)
        date_to = vals.get('date_to',False)
        
        if date_from and len(date_from) > 10:
            date_from = date_from[:10]
        if date_to and len(date_to) > 10:
            date_to = date_to[:10]            
        
        if date_from and len(date_from) == 10: #fromat: 2014-03-20
                date_from = '%s 08:00:00' %date_from
                vals['date_from'] = date_from
                
        if date_to and len(date_to) == 10: #fromat: 2014-03-21
                date_to = '%s 16:00:00' %date_to
                vals['date_to'] = date_to
        return vals

    def message_subscribe_users(self, cr, uid, ids, user_ids=None, subtype_ids=None, context=None):
        """ Do not notify manager if type is 'Feiertag' """
        if ids:
            record = self.browse(cr, uid, ids[0])
            if record.leave_code == 'legal':
                user_ids = []
        
        return super(hr_holidays, self).message_subscribe_users(cr, uid, ids, user_ids=user_ids, subtype_ids=subtype_ids, context=context)

class hr_attendance(osv.osv):
    _inherit='hr.attendance'
    
    def _altern_si_so(self, cr, uid, ids, context=None):
        return True
    
    _columns = {
                'user_id':fields.related('employee_id', 'user_id', type='many2one', relation='res.users', string='User', store=True),
                }
    
    _constraints = [(_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]
    
class hr_timesheet_sheet(osv.osv):
    _inherit='hr_timesheet_sheet.sheet'
    
    def cron_create_monthly_timesheets(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        
        date_from = time.strftime('%Y-%m-01')      
        
        for emp_id in emp_obj.search(cr,uid,[]):
            vals = {}
            sheet_id = self.search(cr,uid,[('employee_id','=',emp_id),('date_from','=',date_from)])
            if not sheet_id:
                try:
                    self.create(cr,uid,{'employee_id':emp_id})
                except:
                    pass
                
        return True
    
class hr_holidays_template(osv.osv):
    _name='hr.holidays.template'
    _description='Holiday Templates'
    

    _columns = {
        'name': fields.char('Name', size=100, required=True),
        'sequence': fields.integer('Sequence',help=_('If there are multiple templates, the one with the lowest sequence is chosen.')),
        'create_employees': fields.boolean('Create holidays for new employees'),
        'line_ids': fields.one2many('hr.holidays.template_line','template_id','Public Holidays',ondelete='cascade'),
    }
    
    _defaults = {    
        'create_employees': True,
        }
    
hr_holidays_template()
    
class hr_holidays_template_line(osv.osv):
    _name='hr.holidays.template_line'
    _order='date'
    
    _columns = {
        'template_id': fields.many2one('hr.holidays.template', 'Template', required=True),
        'name': fields.char('Description', size=100, required=True),
        'date': fields.date('Date',required=True),
    }
    
    _defaults = {    
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        }
        