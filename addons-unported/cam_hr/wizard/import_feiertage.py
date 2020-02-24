# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import openerp
from openerp import netsvc
from openerp.osv import osv, fields
from lxml import etree
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class wizard_feiertage(osv.osv_memory):
    _name ='wizard.import_feiertage'
    _description=u'Importiere Feiertage für Mitarbeiter'
    
    def _alle_mitarbeiter(self, cr, uid, context=None):   
        return self.pool.get('hr.employee').search(cr,uid,[('id','!=',SUPERUSER_ID)])
    
    def _get_first(self, cr, uid, context=None): 
        res = self.pool.get('hr.holidays.template').search(cr,uid,[],limit=1)
        return res or False
    
    def import_feiertage(self,cr,uid,ids,context):
        if context is None:
            context = {}
            
        this = self.browse(cr,uid,ids)[0]

        feiertage = []
        
        for feiertag in this.template_id.line_ids:
            feiertage.append({'date_from':'%s 08:00:00'%feiertag.date,'name':feiertag.name})
        
        context['leave_code'] = 'legal'
        holiday_obj = self.pool.get('hr.holidays')
        wf_service = netsvc.LocalService("workflow")

        feiertage_ids = []
        for employee in this.employee_ids:
            for feiertag in feiertage:
                feiertag['employee_id'] = employee.id
                duplicate_ids = holiday_obj.search(cr,uid,[('employee_id','=',employee.id),
                                                           ('leave_code','=','legal'),
                                                           ('date_from','=',feiertag['date_from'])])
                if not duplicate_ids:
                    new_id = holiday_obj.create(cr,uid,feiertag,context)
                    wf_service.trg_validate(uid, 'hr.holidays', new_id, 'confirm', cr)
                    wf_service.trg_validate(uid, 'hr.holidays', new_id, 'validate', cr)
                    wf_service.trg_validate(uid, 'hr.holidays', new_id, 'second_validate', cr)
                    feiertage_ids.append(new_id)
        
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'cam_hr', 'feiertage_tree')[1]
        
        return {
                    'name': _('Feiertage'),
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'view_id': (view_id,'View'),
                    'res_model': 'hr.holidays',
                    'domain': [('id','in',feiertage_ids)],
                    'target': 'current',
                    'type': 'ir.actions.act_window',
                }

    _columns = {
        'employee_ids':fields.many2many('hr.employee','employee_holidays_rel','curr_id','res_id','Mitarbeiter'),
        'template_id': fields.many2one('hr.holidays.template', _('Template'), required=True),

    }
    
    _defaults = {
                 'employee_ids' : _alle_mitarbeiter,
                 'template_id': _get_first,
                 }
    
wizard_feiertage()