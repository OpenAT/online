# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import time
from datetime import datetime
from openerp.report import report_sxw

DAYS_DE = {
           0: 'Montag',
           1:'Dienstag',
           2:'Mittwoch',
           3:'Donnerstag',
           4:'Freitag',
           5:'Samstag',
           6:'Sonntag'}

MONTHS_DE = {
             1:'Januar',
             2:'Februar',
             3:'März',
             4:'April',
             5:'Mai',
             6:'Juni',
             7:'July',
             8:'August',
             9:'September',
             10:'Oktober',
             11:'November',
             12:'Dezember',
             }

class hr_overtime(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(hr_overtime, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'datetime': datetime,
            'dummy_array': self.dummy_array,
            'sum_projects': self.sum_projects,
            'sum_overtime': self.sum_overtime,
            'translate_date': self._translate_date,
        })
        self.context = context
        
        # Re-Calculate before printing
        if context.get('active_ids'):
            sheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
            sheet_obj._total_sums(cr, uid, context.get('active_ids'))
    
    def dummy_array(self, timesheet):    
        return range(31-len(timesheet.day_details))
    
    def sum_projects(self, o):
        return sum(o.sum_hours)
    
    def _translate_date(self, date_string,type='day'):
        date = datetime.strptime(date_string, '%Y-%m-%d')
        if type=='day':
            return DAYS_DE.get(date.weekday(),'n/a')
        elif type=='month':
            return MONTHS_DE.get(date.month,'n/a')
        else:
            return 'n/a'
    
    
    def sum_overtime(self, sheet):
        res =0
        res = sheet.total_overtime + sheet.sum_overtime
        for correction in sheet.correction_ids:
            res += correction.value_hours
        return res
            

report_sxw.report_sxw('report.hr_timesheet_sheet.sheet.report', 'hr_timesheet_sheet.sheet', 'addons/cam_hr_overtime/report/report_hr_overtime.rml', parser=hr_overtime)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


