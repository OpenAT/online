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

import time
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import *
from mx import DateTime
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp import tools, api
import logging


_logger = logging.getLogger(__name__)

class overtime_correction(osv.osv):
    _name = 'overtime.correction'
    
    _columns = {
        'value_hours': fields.float('Hours', required=True, help="This field is added to the current overtime. For correction please insert a negative value! e.g. -20"),
        'name': fields.char('Description', size=128, required=True, help="Diese Beschreibung wird auf dem Timesheet angedruckt!"),
        'timesheet_id': fields.many2one('hr_timesheet_sheet.sheet', 'Timesheet', required=True, help="Bitte beachten Sie, dass das Timesheet im status 'Entwurf' sein muss!"),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
    }
    
    _defaults = {
        'value_hours': 0,
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        for corr in self.browse(cr,uid,ids):
                if corr.timesheet_id.state in ('confirm', 'done'):
                    raise osv.except_osv(_('Achtung!'), _('Sie können keine Überstundenkorrektur auf ein bereits genehmigtes timesheet durchführen. Setzen Sie das Timesheet auf "Entwurf" und versuchen Sie es nochmal.'))
        return super(overtime_correction,self).write(cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, vals, context=None):
        timesheet_id = vals.get('timesheet_id', False)
        if timesheet_id:
            for sheet in self.pool.get('hr_timesheet_sheet.sheet').browse(cr,uid,[timesheet_id],context=context):
                if sheet.state in ('confirm', 'done'):
                    raise osv.except_osv(_('Achtung!'), _('Sie können keine Überstundenkorrektur auf ein bereits genehmigtes timesheet durchführen. Setzen Sie das Timesheet auf "Entwurf" und versuchen Sie es nochmal.'))
        return super(overtime_correction,self).create(cr, uid, vals, context)
    
    def on_change_employee(self, cr, uid, ids, employee_id, timesheet_id):
        res = {}
        res['value']={}
        res['domain']= {}
        
        res['value']['timesheet_id'] = False
        res['domain']['timesheet_id'] = [('id', 'in', [])]
        if employee_id:
            sheet_ids = self.pool.get('hr_timesheet_sheet.sheet').search(cr,uid,[('employee_id','=',employee_id)])
            if sheet_ids:
                res['value']['timesheet_id'] = timesheet_id if timesheet_id in sheet_ids else sheet_ids[0]
                res['domain']['timesheet_id'] = [('id', 'in', sheet_ids)]
                return res

        return res
            
overtime_correction()

class hr_timesheet_sheet(osv.osv):
    _inherit = 'hr_timesheet_sheet.sheet'
    
    _track = {
        'state': {
            'cam_hr_overtime.mt_state_changed': lambda self, cr, uid, obj, ctx=None: obj['state'] != 'new',
        },
    }
    
    def __init__(self, pool, cr):
        super(hr_timesheet_sheet, self).__init__(pool, cr)
            
    def _total_sums(self, cr, uid, ids, field_name=None, arg=None, context=None):       
        if context is None:
            context={}
        res = {}
        
        for sheet in self.browse(cr, uid, ids):  
            res[sheet.id] = {}
            
            # If the sheet is not in state 'draft' is is not possible to change these values anymore
            if sheet.state == 'draft':
                overtime = 0
                overtime_correction = 0
                planned = 0
                vacation = 0
                vacation_days = 0
                illness = 0
                others = 0
                attendance = 0
                
                for c in sheet.correction_ids:
                    overtime_correction+=c.value_hours
                
                for day in sheet.day_details:
                    overtime = overtime + day.overtime
                    planned = planned + day.planned
                    vacation = vacation + day.vacation
                    if day.vacation > 0:
                        if day.planned > day.vacation:
                            vacation_days = vacation_days + 0.5 # Half day vacation
                        else:
                            vacation_days = vacation_days + 1
                    illness = illness + day.illness
                    others = others + day.others
                    attendance = attendance + day.attendance
                
                res[sheet.id]['total_overtime'] = overtime
                res[sheet.id]['total_overtime_correction'] = overtime_correction
                res[sheet.id]['total_overtime_and_correction'] = overtime + overtime_correction
                res[sheet.id]['total_planned'] = planned
                res[sheet.id]['total_vacation'] = vacation
                res[sheet.id]['total_vacation_days'] = vacation_days
                res[sheet.id]['total_illness'] = illness
                res[sheet.id]['total_others'] = others
                res[sheet.id]['total_attendance2'] = attendance
                
                #check if confirming is allowed
                if context.get('simulation',False):
                    res_db = self.read(cr,uid,sheet.id,['total_overtime','total_overtime_correction','total_overtime_and_correction','total_planned','total_vacation','total_vacation_days','total_illness','total_others','total_attendance2'])
                    if res_db.get('id',False):
                        del res_db['id']
                        
                    for k,v in res_db.iteritems():
                        v_db="%.3f" %v
                        v_curr="%.3f" %res[sheet.id][k]
                        if v_db != v_curr:
                            raise osv.except_osv(_('Timesheet not up to date'), _('Please compute/print your Timesheet again!'))
                
                self.write(cr,uid,sheet.id,res[sheet.id])
   
        return res

    def _vacation_allocations(self, cr, uid, ids, field_name, arg, context=None):       
        """
        This function calculates the sum of all previous timesheets of state 'done' (approved)
        """    
        res = {}
        
        for sheet in self.browse(cr, uid, ids): 

            # Include Vacation Allocations:
            cr.execute('''  SELECT  COALESCE(SUM(number_of_days),0)
                            FROM    hr_holidays h,
                                    hr_employee e,
                                    resource_resource r,
                                    res_company c                            
                            WHERE   type = 'add' AND
                                    e.id = h.employee_id AND
                                    r.id = e.resource_id AND
                                    c.id = r.company_id AND 
                                    h.state = 'validate' AND
                                    h.holiday_status_id = c.vacation_type_id AND
                                    COALESCE(h.effective_date,h.write_date::date) >= %s AND
                                    COALESCE(h.effective_date,h.write_date::date) <= %s AND
                                    e.id = %s''', (sheet.date_from, sheet.date_to, sheet.employee_id.id))
            
            res[sheet.id] = cr.fetchall()[0][0]
        return res

    def _total_sums_all_sheets(self, cr, uid, ids, field_name, arg, context=None):       
        """
        This function calculates the sum of all previous timesheets of state 'done' (approved)
        """    
        res = {}
        
        for sheet in self.browse(cr, uid, ids): 
            res[sheet.id] = {}

            # Include Vacation Allocations:
            cr.execute('''  SELECT  COALESCE(SUM(number_of_days),0)
                            FROM    hr_holidays h,
                                    hr_employee e,
                                    resource_resource r,
                                    res_company c                            
                            WHERE   type = 'add' AND
                                    e.id = h.employee_id AND
                                    r.id = e.resource_id AND
                                    c.id = r.company_id AND 
                                    h.state = 'validate' AND
                                    h.holiday_status_id = c.vacation_type_id AND
                                    COALESCE(h.effective_date,h.write_date::date) < %s AND
                                    e.id = %s''', (sheet.date_from, sheet.employee_id.id))
                                    
            res[sheet.id]['sum_vacation_days'] = cr.fetchall()[0][0]
                                    
            cr.execute('''  SELECT  COALESCE(SUM(total_overtime),0),
                            SUM(total_vacation),                   
                            SUM(total_illness),
                            SUM(total_others),
                            SUM(total_attendance2),
                            SUM(total_planned),
                            COALESCE(SUM(total_vacation_days),0),
                            COALESCE(SUM(total_overtime_correction),0)                        
                    FROM    hr_timesheet_sheet_sheet
                    WHERE   state = 'done' AND
                            date(date_to) < %s AND
                            employee_id = %s''', (sheet.date_from, sheet.employee_id.id))
            
            
        
            result = cr.fetchall()
        
            if(len(result) > 0):  
                res[sheet.id]['sum_overtime'] = result[0][0]+result[0][7] 
                res[sheet.id]['sum_vacation'] = result[0][1]
                res[sheet.id]['sum_illness'] = result[0][2]
                res[sheet.id]['sum_others'] = result[0][3]
                res[sheet.id]['sum_attendance'] = result[0][4]   
                res[sheet.id]['sum_planned'] = result[0][5]  
                
                # Subtract from allocations
                res[sheet.id]['sum_vacation_days'] = res[sheet.id]['sum_vacation_days'] - result[0][6]                                                
            else:
                res[sheet.id]['sum_overtime'] = 0
                res[sheet.id]['sum_vacation'] = 0
                res[sheet.id]['sum_illness'] = 0
                res[sheet.id]['sum_others'] = 0
                res[sheet.id]['sum_attendance'] = 0
                res[sheet.id]['sum_planned'] = 0    
                res[sheet.id]['sum_vacation_days'] = 0   
                                        
        return res
    
    def _state_attendance(self, cr, uid, ids, name, args, context=None):
        emp_obj = self.pool.get('hr.employee')
        result = {}
        link_emp = {}
        emp_ids = []

        for sheet in self.browse(cr, uid, ids, context=context):
            result[sheet.id] = 'none'
            emp_ids2 = emp_obj.search(cr, uid,
                    [('user_id', '=', sheet.user_id.id)], context=context)
            if emp_ids2:
                link_emp[emp_ids2[0]] = sheet.id
                emp_ids.append(emp_ids2[0])
        for emp in emp_obj.browse(cr, uid, emp_ids, context=context):
            if emp.id in link_emp:
                sheet_id = link_emp[emp.id]
                result[sheet_id] = emp.state
        return result
        
    _columns = {
        'total_planned': fields.float(string='Planned Hours', readonly=True),
        'total_overtime': fields.float(string='Overtime', readonly=True),
        'total_overtime_correction': fields.float(string='Overtime Corrections', readonly=True),
        'total_overtime_and_correction': fields.float(string='Total Overtime', readonly=True),
        'total_vacation': fields.float(string='Vacation', readonly=True),
        'total_illness': fields.float(string='Illness', readonly=True),
        'total_others': fields.float(string='Others', readonly=True),
        'total_attendance2': fields.float(string='Attendance'),
        'total_vacation_days': fields.float(string='Vacation in days', readonly=True),
        'sum_overtime': fields.function(_total_sums_all_sheets, multi='_total_sums_all_sheets', string='Sum Overtime', readonly=True, help="Total overtime in hours of all previous timesheets in state 'done'"),
        'sum_vacation': fields.function(_total_sums_all_sheets, multi='_total_sums_all_sheets', string='Sum Vacation', readonly=True, help="Total vacation in hours of all previous timesheets in state 'done'"),   
        'sum_vacation_days': fields.function(_total_sums_all_sheets, multi='_total_sums_all_sheets', string='Sum Vacation in days', readonly=True, help="Total vacation in days of all previous timesheets in state 'done'"),    
        'sum_illness': fields.function(_total_sums_all_sheets, multi='_total_sums_all_sheets', string='Sum Illness', readonly=True, help="Total illness in hours of all previous timesheets in state 'done'"),    
        'sum_others': fields.function(_total_sums_all_sheets, multi='_total_sums_all_sheets', string='Sum Others', readonly=True, help="Total illness in hours of all previous timesheets in state 'done'"), 
        'sum_attendance': fields.function(_total_sums_all_sheets, multi='_total_sums_all_sheets', string='Sum Attendance', readonly=True, help="Total illness in hours of all previous timesheets in state 'done'"), 
        'sum_planned': fields.function(_total_sums_all_sheets, multi='_total_sums_all_sheets', string='Sum Planned', readonly=True, help="Total illness in hours of all previous timesheets in state 'done'"),  
        'day_details': fields.one2many('hr_timesheet_sheet.sheet.day_detail', 'sheet_id', 'Day Details', readonly=True),
        'vacation_alloc_days': fields.function(_vacation_allocations, string='Vacation Allocations'),
        'project_hours' : fields.one2many('hr_timesheet_sheet.sheet.project_hours', 'sheet_id', 'Project Hours', readonly=True),
        'correction_ids' : fields.one2many('overtime.correction', 'timesheet_id', 'Overtime Corrections',readonly=True),
        'state_attendance' : fields.function(_state_attendance, type='selection', selection=[('absent', 'Absent'), ('present', 'Present'), ('present_out', 'Present (Out of Office)'),('none','No employee defined')], string='Current Status'),
        #'remaining_leaves': fields.related('employee_id', 'remaining_leaves', type='function', string='Remaining Legal Leaves')
    }
    
    def _default_name(self,cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        
        date_from = self._default_date_from(cr, uid, context)
        datetime.strptime(date_from, '%Y-%m-%d')
        
        if r=='month':
            return time.strftime('%Y-%m')
        elif r=='week':
            return (datetime.today() + relativedelta(weekday=0, weeks=-1)).strftime('%Y-%m-%d')
        elif r=='year':
            return time.strftime('%Y')
    
    _defaults = {
        'name' : _default_name
    }
    
    def name_get(self, cr, user, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        sheets = self.browse(cr,user,ids,context)
        result = []
        for s in sheets:
            result.append((s.id,datetime.strptime(s.date_from, '%Y-%m-%d').strftime('%Y %B')))
        return result
    
    def button_lunch(self, cr, uid, ids, context=None):
        att_obj = self.pool.get('hr.attendance')
        comp_obj = self.pool.get('res.company')
        company_id = comp_obj._company_default_get(cr, uid, 'hr.attendance', context=context)
        company = comp_obj.browse(cr, uid, company_id, context=context)
        
        if not company.lunch_duration:
            raise osv.except_osv(_('Error'), _("Please specify a 'Lunch Duration' in the company configuration!")) 
        
        # time of sign_out is always 12:00
        lunch_time = DateTime.now() + DateTime.RelativeDateTime(hour=10, minute=0, second=0)
        
        for sheet in self.browse(cr, uid, ids):      
            vals = {
                'name': lunch_time.strftime('%Y-%m-%d %H:%M:%S'),
                'sheet_id': sheet.id,
                'action': 'sign_out',
                'flag': 'B',
                'employee_id': sheet.employee_id.id,
            }         
            att_obj.create(cr, uid, vals, context=context)
            vals['name'] = (lunch_time + DateTime.RelativeDateTime(minutes= company.lunch_duration)).strftime('%Y-%m-%d %H:%M:%S')
            vals['action'] = 'sign_in'
            att_obj.create(cr, uid, vals, context=context)
        
        return True
   
    def button_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
            
        #compute values
        context['simulation'] = True
        self._total_sums(cr, uid, ids,context=context)
        res = super(hr_timesheet_sheet,self).button_confirm(cr,uid,ids,context=context)
        if res:
            # get res.company value for max_difference_day
            company_obj = self.pool.get('res.company')
            company_id = company_obj._company_default_get(cr, uid, 'hr_timesheet_sheet.sheet')
            company = company_obj.browse(cr, uid, company_id)
            if company.max_difference_day and company.max_difference_day > 0:
                for sheet in self.browse(cr,uid,ids):
                    cr.execute('SELECT day.name FROM hr_timesheet_sheet_sheet AS sheet \
                    LEFT JOIN hr_timesheet_sheet_sheet_day AS day \
                    ON (sheet.id = day.sheet_id) \
                    WHERE sheet.id IN %s \
                    AND day.total_difference*60 > %s',(tuple(ids),(company.max_difference_day)))
                    x = cr.fetchall()
                    if len(x)>0:
                        raise osv.except_osv(_('Cannot confirm Timesheet!'), _('The difference per day exceeds the maximum of %s minutes for the timesheet: "%s".\nPlease correct the following days:: \n %s')%(company.max_difference_day,sheet.name,x))
        return res
        
    def button_compute(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        self._total_sums(cr, uid, ids,context=context)
        return True

    def create(self, cr, uid, values, context=None):
        timesheet = super(hr_timesheet_sheet, self).create(cr, uid, values, context=context)
        try:
            ts = self.browse(cr, SUPERUSER_ID, [timesheet, ])
            if ts.employee_id.contract_id.default_overtime:
                # Add default overtime
                overtime = {
                    'value_hours': ts.employee_id.contract_id.default_overtime,
                    'name': _('Default Overtime from Employee Contract'),
                    'timesheet_id': ts.id,
                    'employee_id': ts.employee_id.id,
                }
                overtime_obj = self.pool.get('overtime.correction')
                overtime_obj.create(cr, SUPERUSER_ID, overtime, context=context)
        except:
            _logger.warning('Could not create default overtime from employee contract for timesheet.')
        return timesheet

hr_timesheet_sheet()





class hr_timesheet_sheet_sheet_day_detail(osv.osv):
    _name = "hr_timesheet_sheet.sheet.day_detail"
    _description = "Days by Period"
    _auto = False
    _order='name'
            
    def _attendance(self, cr, uid, ids, field_name, arg, context=None):       
        res = {}
        for day_detail in self.browse(cr, uid, ids):       
            cr.execute('''  SELECT  total_attendance
                            FROM    hr_timesheet_sheet_sheet_day
                            WHERE   sheet_id = ''' + str(day_detail.sheet_id.id) + 
                          ' AND     name = \'' + str(day_detail.name) + '\'')
            
            result = cr.fetchall()
            
            if len(result) == 0:
                res[day_detail.id] = 0
            else:              
                res[day_detail.id] = result[0][0]
        return res   

        
    def _leaves(self, cr, uid, ids, field_name, arg, context=None):       
        res = {}
        
        for day_detail in self.browse(cr, uid, ids):
            company = day_detail.sheet_id.employee_id.company_id
            vacation_type = -1
            illness_type = -2
            if company:
                if company.vacation_type_id:
                    vacation_type = company.vacation_type_id.id
                if company.illness_type_id:
                    illness_type = company.illness_type_id.id                    
            
            res[day_detail.id] = {}
            # Check leaves
            cr.execute('''  SELECT  hs.id, count(*), bool_and(h.half_day)
                            FROM    hr_holidays h,
                                    hr_holidays_status hs
                            WHERE   h.holiday_status_id = hs.id
                            AND     employee_id = %s
                            AND     date(date_from) <= %s 
                            AND     date(date_to) >= %s 
                            AND     state='validate' 
                            AND     type = 'remove'
                            AND     holiday_type = 'employee'
                            GROUP BY hs.id
                            ''', (day_detail.sheet_id.employee_id.id, day_detail.name, day_detail.name))
            r = cr.fetchall()
            
            planned=day_detail.planned            
            res[day_detail.id]['vacation'] = 0
            res[day_detail.id]['illness'] = 0
            res[day_detail.id]['others'] = 0
            #res[day_detail.id]['real_planned'] = planned
            
            for row in r:
                if row[0] == vacation_type:
                    if row[1] > 0:
                        if row[2]:
                            vac = 0.5 # Half day
                        else:
                            vac = 1 # Full day
                    else:
                        vac = 0
                    res[day_detail.id]['vacation'] = vac * planned
                elif row[0] == illness_type:
                    res[day_detail.id]['illness'] = (row[1] > 0 and 1 or 0) * planned
                else:
                    res[day_detail.id]['others'] = (row[1] > 0 and 1 or 0) * planned
            
            if res[day_detail.id]['others']:
                res[day_detail.id]['vacation'] = 0
                res[day_detail.id]['illness'] = 0
            if res[day_detail.id]['illness']:
                res[day_detail.id]['vacation'] = 0     
            
            leave_in_hours = max([res[day_detail.id]['others'], res[day_detail.id]['vacation'], res[day_detail.id]['illness']])
            res[day_detail.id]['real_planned'] = planned - leave_in_hours
            
        return res
        

    def _overtime(self, cr, uid, ids, field_name, arg, context=None):       
        res = {}
        for day_detail in self.browse(cr, uid, ids):
            res[day_detail.id] = 0
            if datetime.strptime(day_detail.name, '%Y-%m-%d') <= datetime.today():
                res[day_detail.id] = day_detail.attendance + day_detail.vacation + day_detail.illness + day_detail.others - day_detail.planned
                if day_detail.vacation > 0 and day_detail.others > 0:
                    res[day_detail.id] -= day_detail.vacation
                
        return res;  
    
    _columns = {
        'name': fields.date('Date', readonly=True),
        'sheet_id': fields.many2one('hr_timesheet_sheet.sheet', 'Sheet', readonly=True, select="1"),
        'employee_id': fields.many2one('hr.employee', 'Employee', readonly=True, select="1"),
        'attendance': fields.function(_attendance, string='Attendance', type='float', readonly=True),
        #'planned': fields.function(_planned_hours, string='Planned', readonly=True),
        'planned': fields.float('Planned Hours', readonly=True),
        'vacation': fields.function(_leaves, string='Vacation', type='float', multi='_leaves', readonly=True),
        'illness': fields.function(_leaves, string='Illness', type='float', multi='_leaves', readonly=True),
        'others': fields.function(_leaves, string='Other Leaves', type='float', multi='_leaves', readonly=True),
        'overtime': fields.function(_overtime, string='Overtime', type='float', readonly=True),
        'real_planned': fields.function(_leaves, string='Planned', type='float', multi='_leaves', readonly=True),
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_timesheet_sheet_sheet_day_detail')
        cr.execute("""  CREATE OR REPLACE VIEW hr_timesheet_sheet_sheet_day_detail as (
                            select ((day::date - date '2014-01-01')*100000)+emp.id as id, 
    day::date as name,emp.id as employee_id,coalesce(planned.planned,0.0) as planned, planned.contract_id,sh.id as sheet_id
    from generate_series('2014-01-01'::timestamp, (now()+ interval '30 days')::timestamp, '1 day') as period(day) cross join hr_employee emp 
    left join hr_timesheet_sheet_sheet sh
                            ON      (date_from <= day AND
                                    date_to >= day and emp.id = sh.employee_id)
    left join
        (select dayofweek, c.employee_id,c.id as contract_id, c.date_start,c.date_end, hour_to-hour_from as planned from resource_calendar_attendance a, 
                                                            resource_calendar r, 
                                                            hr_contract c
            where a.calendar_id = r.id and
            c.working_hours = r.id ) planned 
            
    on (day >= planned.date_start and day <= coalesce(planned.date_end, (now()+ interval '30 days')::date) and 
        (extract(dow from day)::integer = (dayofweek::integer + 1) % 7) and planned.employee_id=emp.id)
    order by sheet_id,employee_id,sheet_id)""")
                             
hr_timesheet_sheet_sheet_day_detail()


class hr_timesheet_sheet_sheet_project_hours(osv.osv):
    _name = "hr_timesheet_sheet.sheet.project_hours"
    _description = "Project hours per period"
    _auto = False      
    _order = "sheet_id, sum_hours DESC"
    _rec_name = 'account_id'      
   
    _columns = {
        'account_id': fields.many2one('account.analytic.account', 'Project', readonly=True, select="1"),
        'sheet_id': fields.many2one('hr_timesheet_sheet.sheet', 'Sheet', readonly=True, select="1"),
        'sum_hours': fields.float('Hours spent', readonly=True),
    }
    
    def init(self, cr):
        cr.execute("""  CREATE OR REPLACE VIEW hr_timesheet_sheet_sheet_project_hours as (
                        SELECT  sheet.id * 100000 + line.account_id AS id, 
                                sheet.id AS sheet_id, 
                                line.account_id, 
                                sum(line.unit_amount) AS sum_hours
                        FROM    account_analytic_line line, 
                                hr_employee e,
                                resource_resource r,
                                hr_timesheet_sheet_sheet sheet
                        WHERE   line.date >= sheet.date_from AND 
                                line.date <= sheet.date_to AND 
                                line.user_id = sheet.user_id AND
                                e.resource_id = r.id AND
                                r.user_id = sheet.user_id AND
                                e.journal_id = line.journal_id
                        GROUP BY     line.account_id, sheet.id)""")
                             
hr_timesheet_sheet_sheet_project_hours()


class resource_calendar(osv.osv):
    _inherit="resource.calendar"
    
    def write(self, cr, uid, ids, vals, context=None):
        for resource in self.browse(cr,uid,ids):
            sheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
            contract_obj = self.pool.get('hr.contract')
            contract_ids = contract_obj.search(cr,uid,[('working_hours','=',resource.id)])
            if contract_ids:
                for contract in contract_obj.browse(cr,uid,contract_ids):
                    sheet_ids = sheet_obj.search(cr,uid,[('state','in',['done','confirm']),
                                                 ('date_from','=',contract.date_start)])
                    if sheet_ids:
                        raise osv.except_osv(_('Arbeitszeiten ändern'), _("Sie können die Arbeitszeiten nicht ändern, da es schon eine Zeiterfassung gibt, die sich im Status 'bestätigt' oder 'erledigt' befindet."))
        super(resource_calendar, self).write(cr, uid, resource.id, vals, context)
        return True 
    

# Add 2 constraints:
#  - it is only allowed to start a contract on the first of a month
#  - 2 contracts of the same employee should not overlap
class hr_contract(osv.osv):
    _inherit = "hr.contract"

    #default_overtime = Float(string='Default Overtime')
    _columns = {
        'default_overtime': fields.float(string='Default Overtime', readonly=False),
    }

    def write(self, cr, uid, ids, vals, context):
        if vals.get('working_hours',False) or vals.get('date_start',False) or vals.get('employee_id',False):
            contract = self.browse(cr,uid,ids)[0]
            sheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
            sheet_ids = sheet_obj.search(cr,uid,[('employee_id','=',contract.employee_id.id),
                                                 ('state','in',['done','confirm']),
                                                 ('date_from','=',contract.date_start)])
            if sheet_ids:
                raise osv.except_osv(_('Vertrag ändern'), _("Sie können den Vertrag nicht ändern. Legen Sie einen neuen Vertrag für diesen Mitarbeiter an oder setzen Sie die Zeiterfassung auf 'Entwurf' zurück."))
        return super(hr_contract,self).write(cr,uid,ids,vals,context)
    
    def _get_type(self, cr, uid, context=None):
        try:
            return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_contract', 'hr_contract_type_emp')[1]
        except ValueError:
            return False
        
    def _get_first_month(self, cr, uid, context=None):
        return "%s-%s-%s" %(time.strftime('%Y'),time.strftime('%m'),"01")

        
    def _check_overlap(self, cr, uid, ids, context=None):
        for contract in self.read(cr, uid, ids, ['id','date_start','date_end','employee_id'], context=context):
            if not contract['date_end']:
                contract['date_end'] = '9999-12-31'
                
            cr.execute("SELECT  1 \
                        FROM    hr_contract \
                        WHERE   (DATE %s, DATE %s) OVERLAPS (date_start, COALESCE(date_end, DATE '9999-12-31')) is true \
                        AND     employee_id=%s \
                        AND     id <> %s",(contract['date_start'], contract['date_end'], contract['employee_id'][0], contract['id']))
            if cr.fetchall():
                return False
        return True
    
    _defaults = {
        'date_start': _get_first_month,
        'type_id': _get_type,
        'wage':0,
    }
    
    _constraints = [
        (_check_overlap, 'You can not have 2 contracts that overlap !', ['date_start','date_end','employee_id'])
    ]
    
hr_contract()


class hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"
    
    _columns = {
        'code': fields.char('Code', size=16),
    }

hr_holidays_status()


# Update the calculation of the 'number_of_days'-field
# Therefore consider weekends and the working schedule of the employee
class hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    
    def status_get(self, cr, uid, context=None):
        if context is None:
            context = {}
        leave_code = context.get('leave_code',False)
        if leave_code:
            res = self.pool.get('hr.holidays.status').search(cr,uid,[('code','=',leave_code)],limit=1)
            if res:
                return res[0]
            else:
                raise osv.except_osv(_('Konfigurationsfehler'), _("Abwesenheitstyp: '%s' ist nicht konfiguriert!" % leave_code))
                
        return False
    
    def _check_date(self, cr, uid, ids):
        for holiday in self.browse(cr, uid, ids):
            holiday_ids = self.search(cr, uid, [('date_from', '<=', holiday.date_to), 
                                                ('date_to', '>=', holiday.date_from), 
                                                ('employee_id', '=', holiday.employee_id.id), 
                                                ('id', '<>', holiday.id),
                                                ('holiday_status_id','=',holiday.holiday_status_id.id),
                                                ('type','=',holiday.type)])
            if holiday_ids:
                return False
        return True
        
    _columns = {
        'leave_code':fields.related('holiday_status_id', 'code', string='Leave Code', type='char', readonly=True, store=True),
        'user_id':fields.related('employee_id', 'user_id', type='many2one', relation='res.users', string='User', store=True),
        'effective_date': fields.date('Effective date', readonly=True, states={'draft':[('readonly',False)]}, help='This is the date when this allocation becomes effective.'),
        'half_day': fields.boolean('Halber Tag', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, track_visibility='onchange'),
        'date_from': fields.datetime('Datum von', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, select=True, copy=False, track_visibility='onchange'),
        'date_to': fields.datetime('Datum bis', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, copy=False, track_visibility='onchange'),      
    }
    
    _defaults = {
        'holiday_status_id': status_get,
        'date_from': fields.date.context_today,
        'date_to':fields.date.context_today, 
        'effective_date':fields.date.context_today, 
    }
    
    _constraints = [
        (_check_date, 'Es existiert bereits eine Abwesenheit des selben Typs (Urlaub, Krankenstand, Feiertag) für diesen Mitarbeiter, in diesem Zeitraum!', ['date_from','date_to']),
    ] 
 

    def holidays_confirm(self, cr, uid, ids, context=None):
        ''' It is only allowed to confirm a holiday if the affected timesheets are in state 'draft' '''
        for holiday in self.browse(cr, uid, ids):
            # Only check Leave Requests
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                cr.execute('''SELECT    1
                    FROM     hr_timesheet_sheet_sheet s
                    WHERE    (s.date_from, s.date_to) OVERLAPS (DATE %s - INTERVAL '1 day', DATE %s + INTERVAL '1 day')
                    AND      s.state <> 'draft'
                    AND      employee_id = %s''', (holiday.date_from, holiday.date_to, holiday.employee_id.id))   
            
                if cr.rowcount > 0:
                    raise osv.except_osv(_('Invalid action !'), _("Cannot approve leave if the related timesheet(s) are not in state 'draft'"))
            
        return super(hr_holidays,self).holidays_confirm(cr, uid, ids, context)
    
    def holidays_validate(self, cr, uid, ids, context=None):
        ''' It is only allowed to approve a holiday if the affected timesheets are in state 'draft' '''
        
        for holiday in self.browse(cr, uid, ids):
            # Only check Leave Requests
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                cr.execute('''SELECT    1
                    FROM     hr_timesheet_sheet_sheet s
                    WHERE    (s.date_from, s.date_to) OVERLAPS (DATE %s - INTERVAL '1 day', DATE %s + INTERVAL '1 day')
                    AND      s.state <> 'draft'
                    AND      employee_id = %s''', (holiday.date_from, holiday.date_to, holiday.employee_id.id))   
            
                if cr.rowcount > 0:
                    raise osv.except_osv(_('Invalid action !'), _("Cannot approve leave if the related timesheet(s) are not in state 'draft'"))
            
        return super(hr_holidays,self).holidays_validate(cr, uid, ids, context)
    
    def holidays_refuse(self, cr, uid, ids, context=None):
        ''' It is only allowed to refuse a holiday if the affected timesheets are in state 'draft' '''
        
        for holiday in self.browse(cr, uid, ids):
            # Refusing in state 'confirmed' is allowed
            if holiday.holiday_type == 'employee' and holiday.state == 'validate' and holiday.date_from:
                cr.execute('''SELECT    1
                        FROM     hr_timesheet_sheet_sheet s
                        WHERE    (s.date_from, s.date_to) OVERLAPS (DATE %s - INTERVAL '1 day', DATE %s + INTERVAL '1 day')
                        AND      s.state <> 'draft'
                        AND      employee_id = %s''', (holiday.date_from, holiday.date_to, holiday.employee_id.id))   
                
                if cr.rowcount > 0:
                    raise osv.except_osv(_('Invalid action !'), _("Cannot refuse leave if the related timesheet(s) are not in state 'draft'"))
            
        return super(hr_holidays,self).holidays_refuse(cr, uid, ids, context)    
        
hr_holidays()


class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
        'time_credit': fields.integer('Time Credit', required=True,
                                      help='Time credit in minutes when doing SignIn/SignOut'),
        'max_difference_day': fields.integer('Max difference per Day', required=True,
                                      help='Max difference per day in minutes. If difference is higher, it will raise a warning each sign in/sign out with the specific days. User wont be able to confirm the timesheet, if there are >1 days.\nThis check is only active if value > 0.'),
        'lunch_duration': fields.integer('Lunch Duration', help='Lunch duration in minutes (used for Lunch-button)'),
        'vacation_type_id': fields.many2one('hr.holidays.status', 'Holiday state of vacation'),
        'illness_type_id': fields.many2one('hr.holidays.status', 'Holiday state of illness'),  
              
    }
    
    def _get_default_vacation_type(self, cr, uid, context=None):
        try:
            return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'cam_hr_overtime', 'holiday_status_vacation')[1]
        except ValueError:
            return False
    
    def _get_default_illness_type(self, cr, uid, context=None):
        try:
            return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'cam_hr_overtime', 'holiday_status_krankenstand')[1]
        except ValueError:
            return False
    
    _defaults = {
        'time_credit': 0,
        'max_difference_day':  0,
        'lunch_duration': 60,
        'timesheet_range':'month',
        'vacation_type_id': _get_default_vacation_type,
        'illness_type_id': _get_default_illness_type,
    }
res_company()


class hr_attendance(osv.osv):
    _inherit = 'hr.attendance'
    
    _columns = {
                'flag': fields.selection([('M', 'Manual'), ('B', 'Button'), ('T','Terminal')], 'Flag', readonly=True, 
                                         help="(Manual) If you create/modifiy manually.\n(Button) If you create your sign in/sign outs with the 'sign in/sign out' buttons\n(Terminal) Created by the Terminal"),
                }
    
    def _get_default_date(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = datetime.now() + timedelta(seconds=-datetime.now().second)
        if 'name' in context:
            return context['name'] + now.strftime(' %H:%M:%S')
        return now.strftime('%Y-%m-%d %H:%M:%S')
    
    
    def write(self, cr, uid, ids, vals, context):
        if len(vals)>0 and 'name' in vals:
            vals['flag'] = 'M'
        return super(hr_attendance,self).write(cr, uid, ids, vals, context)
    
    _defaults = {
        'flag': 'M',
        'name': _get_default_date,
    }
hr_attendance()


class hr_employee_timesheet_report(osv.osv):
    _name = "hr_employee.timesheet.report"
    _description = "Timesheet report per employee"
    _auto = False
    _order='employee_id, date desc'
    
    _columns = {
        'employee_id': fields.many2one('hr.employee','Employee', readonly=True),
        'date': fields.date('date', readonly=True, select="1", group_operator="max"),
        'name': fields.char('Description', size=128, readonly=True),
        'overtime': fields.float(string='Overtime', readonly=True),
        'vacation': fields.float(string='Vacation', readonly=True),
        'month': fields.char('Monat', size=10, readonly=True, help="Monat"),
        'year': fields.char('Jahr', size=4, readonly=True, help="Jahr"),
        
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_employee_timesheet_report')
        cr.execute("""  CREATE OR REPLACE VIEW hr_employee_timesheet_report as (
                           select   main.id,  
                                    main.employee_id, 
                                    main.date, 
                                    to_char(main.date, 'YYYY') as year,
                                    to_char(main.date, 'MM/YYYY') as month,
                                    main.name,
                                    main.vacation,
                                    main.overtime
                                FROM
                                    (SELECT   h.id * 10 + 1 as id,
                                        h.employee_id as employee_id,
                                        COALESCE(h.effective_date,h.write_date::date) as date, 
                                        h.name, 
                                        COALESCE(h.number_of_days,0) as vacation,
                                        0 as overtime
                                    FROM    hr_holidays h,
                                            hr_employee e,
                                            resource_resource r,
                                            res_company c
                                    WHERE   type = 'add' AND
                                        e.id = h.employee_id AND
                                        r.id = e.resource_id AND
                                        c.id = r.company_id AND 
                                        state = 'validate' AND
                                        h.holiday_status_id = c.vacation_type_id AND
                                        h.holiday_type = 'employee'
                                    UNION
                                
                                    SELECT  s.id * 10 + 2 as id,
                                        s.employee_id as employee_id,
                                        s.date_from as date,
                                        s.name as name,
                                        COALESCE(-total_vacation_days,0) as vacation,
                                        COALESCE(total_overtime,0) as overtime
                                    FROM    hr_timesheet_sheet_sheet s
                                    WHERE   state = 'done'
                                
                                    UNION
                                
                                    SELECT  c.id * 10 + 3 as id,
                                        s.employee_id as employee_id,
                                        s.date_from as date,
                                        c.name as name,
                                        0 as vacation,
                                        value_hours as overtime
                                    FROM    overtime_correction c,
                                        hr_timesheet_sheet_sheet s,
                                        hr_employee e,
                                        resource_resource r
                                    WHERE   s.state = 'done' AND
                                        c.timesheet_id = s.id) as main,
                                    hr_employee e,
                                    resource_resource r
                                WHERE    main.employee_id = e.id AND
                                    e.resource_id = r.id AND
                                        r.active is true)""")
                             
hr_employee_timesheet_report()
