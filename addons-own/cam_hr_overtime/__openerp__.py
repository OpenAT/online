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


{
    'name': 'Manage Overtime',
    'version': '1.0',
    'category': 'Custom',
    'description': """
     (1) Extends the timesheet with a 'Summary' tab which displays vacation, illness, other leaves, attendance and overtime on a daily view.
     (2) There are some minor changes in hr_holiday module (calculation of number_of_days) and the hr_contract module (new constraints). 
     (3) A new timesheet report lists the current month as well as the current overtime and vacation.
     (4) Overtime Correction
     (5) Sets seconds to zero and allows to add/subtract a number of minutes.
     (6) Scheduler which checks every timesheet and creates a request if the difference is too high 
     (7) Out of Office Sign in / Out of Office Sign out
     (8) "Lunch" button
    """,
    'author': 'Andreas Brueckl',
    'website': 'http://www.camadeus.at',
    'depends': ['hr', 'hr_contract', 'hr_timesheet', 'hr_timesheet_sheet', 'hr_holidays', 'sale_service'],
    'data': [
        'cam_hr_overtime_data.xml',
        'timesheet_sheet_view.xml',
        'security/ir.model.access.csv',
        'cam_hr_overtime_report.xml',
        'overtime_correction_view.xml',
        'res_config_view.xml',
        'report/overtime_report_view.xml',
        'report/report_overtime_qweb.xml',
    ],
    'installable': True,
    'active': False,
}
