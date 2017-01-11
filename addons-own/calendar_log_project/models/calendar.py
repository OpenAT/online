# -*- coding: utf-8 -*-

from openerp import tools, api
from openerp.fields import Many2one, Boolean, Char, Float, Date, One2many
from openerp.osv import fields, osv
from openerp.tools.translate import _

class calendar_event_category(osv.osv):
    _inherit = 'calendar.event.category'

    is_worklog = Boolean(string='Is Worklog',
                         help='Default Is Worklog setting for meetings with this category',
                         default=False)
    is_attendance = Boolean(string='Is Attendance',
                         help='Default Is-Attendance setting for meetings with this category',
                         default=False)

class hr_analytic_timesheet(osv.osv):
    _inherit = 'hr.analytic.timesheet'
    event_category_id = Many2one('calendar.event.category', string='Event Category', readonly=False)


class calendar_event(osv.osv):
    _inherit = 'calendar.event'

    is_worklog = Boolean(string='Is Worklog', help='Create a Work-Log Entry', default=False)
    is_attendance = Boolean(string='Is Attendance', help='Create Attendance Entry (Sing In/Out)', default=False)
    project_id = Many2one('project.project', string='Project')
    task_id = Many2one('project.task', string='Task')
    worklog_text = Char('Work-Log', size=128)
    task_work_id = Many2one('project.task.work', string='Task Worklog ID')
    analytic_time_id = Many2one('hr.analytic.timesheet', string='HR Analytic Timesheet ID')
    sign_in_id = Many2one('hr.attendance', string='Sign In')
    sign_out_id = Many2one('hr.attendance', string='Sign Out')

    # DISABLED FOR NOW Update the field event_category_id at installation or update
    # def init(self, cr, context=None):
    #     print "INIT OF calendar_log_project"
    #     events = self.browse(cr, SUPERUSER_ID, self.search(cr, SUPERUSER_ID, []))
    #     for event in events:
    #         # We trigger the write method at install or update time for all events to update the event_category_id
    #         event.write({"name": event.name or None})

    @api.onchange('category_id')
    def _oc_category_id(self):
        # Only update if a category was set
        if self.category_id:
            # Set boolean field is_worklog to category setting
            self.is_worklog = self.category_id.is_worklog
            # Set boolean field is attendance to category setting
            self.is_attendance = self.category_id.is_attendance


    @api.onchange('task_id')
    def _set_project(self):
        if self.task_id:
            # Set the Project to the project_id of the Task
            if self.project_id != self.task_id.project_id:
                self.project_id = self.task_id.project_id
            # Set the Main Partner to the task or project partner
            if not self.mainpartner_id:
                if self.task_id.partner_id:
                    self.mainpartner_id = self.task_id.partner_id
                elif self.project_id.partner_id:
                    self.mainpartner_id = self.project_id.partner_id

    @api.onchange('project_id')
    def _set_task(self):
        # https://github.com/odoo/odoo/issues/4574
        if self.project_id:
            # Clear the Task if it has a different project_id
            if self.task_id:
                if self.task_id.project_id != self.project_id:
                    self.task_id = False

            # Try to set the Main Partner
            if not self.mainpartner_id:
                if self.task_id and self.task_id.partner_id:
                    self.mainpartner_id = self.task_id.partner_id
                elif self.project_id.partner_id:
                    self.mainpartner_id = self.project_id.partner_id

            # Set a domain for the task list to only show tasks that belong to this project
            return {'domain': {'task_id': [('project_id', '=', self.project_id.id)]}}
        else:
            # Clear the Domain for Tasks if no Project is selected
            return {'domain': {'task_id': []}}

    # @api.multi
    # def create(self, values, context=None):
    #     return super(calendar_event, self).create(values, context=context)

    @api.multi
    def write(self, values):
        # WARNING: Check that NO defaults are set for is_worklog and is_attendance fields cause this will make it
        #          impossible for other code to create events. MUST BE FALSE BY DEFAULT!
        assert not self.env['ir.values'].sudo().search(
            ['&', ('name', '=', 'is_worklog'), ('model', '=', 'calendar.event')]), _(
            'Remove any Default for calendar.event.is_worklog field! Settings > Technical > Actions > User Defaults')
        assert not self.env['ir.values'].sudo().search(
            ['&', ('name', '=', 'is_attendance'), ('model', '=', 'calendar.event')]), _(
            'Remove any Default for calendar.event.is_attendance field! Settings > Technical > Actions > User Defaults')

        # HINT: A event creation will also call the write method because of the "message_last_post" field
        #       Therefore we do not have to extend the create method also.
        # WARNING: Do nothing if record gets unlinked (there is {'active': False} included in vals on unlink)
        if self.ensure_one() and values.get('active', 'Not Included') is not False:
            # Prepare variables
            # HINT: self.task_id.id will return FALSE if self.task_id is empty (no assertion will be thrown!)
            name = values.get('name') if 'name' in values else self.name
            start = values.get('start') if 'start' in values else \
                values.get('start_datetime') if 'start_datetime' in values \
                else self.start
            stop = values.get('stop') if 'stop' in values else \
                values.get('stop_datetime') if 'stop_datetime' in values \
                else self.stop
            duration = values.get('duration') if 'duration' in values else self.duration
            is_worklog = values.get('is_worklog') if 'is_worklog' in values else self.is_worklog
            worklog_text = values.get('worklog_text') if 'worklog_text' in values else self.worklog_text
            is_attendance = values.get('is_attendance') if 'is_attendance' in values else self.is_attendance
            user_id = values.get('user_id') if 'user_id' in values else self.user_id.id
            category_id = values.get('category_id') if 'category_id' in values else self.category_id.id
            project_id = values.get('project_id') if 'project_id' in values else self.project_id.id
            task_id = values.get('task_id') if 'task_id' in values else self.task_id.id

            # =======
            # WORKLOG
            # =======
            # Unlink task worklog
            if task_id != self.task_id.id or not is_worklog:
                # Unlink task worklog and related analytic timesheet worklog
                if self.task_work_id:
                    if self.task_work_id.hr_analytic_timesheet_id:
                        self.task_work_id.hr_analytic_timesheet_id.unlink()
                    self.task_work_id.unlink()

            # Unlink project worklog
            if project_id != self.project_id.id or not is_worklog:
                if self.analytic_time_id:
                    self.analytic_time_id.unlink()

            # Create or update worklog
            if is_worklog:
                assert project_id, _('You have to choose a project if Is Worklog is checked!')

                # Task worklog entry
                # HINT: You can add bool in but it's not necessary, because bool is a subclass of int.
                if task_id:
                    task_worklog_values = {
                        'name': worklog_text or name,
                        'user_id': user_id,
                        'date': start,
                        'hours': duration,
                        'task_id': task_id,
                    }
                    # Update an existing task worklog
                    # HINT: If the task changed the task worklog would already be deleted before we reach this point.
                    if self.task_work_id:
                        self.task_work_id.write(task_worklog_values)
                    # Create a new task worklog
                    # HINT: We did not write the event so need to create the worklog without self.task_work_id
                    else:
                        task_obj = self.env['project.task']
                        task = task_obj.browse([task_id])
                        task_work_id = task.work_ids.create(task_worklog_values)
                        # HINT: task.work_ids will create a related hr_analytic_timesheet entry on creation
                        task_work_id.hr_analytic_timesheet_id.event_category_id = category_id
                        values['task_work_id'] = task_work_id.id
                # Project worklog entry
                else:
                    # Prepare values
                    ts_obj = self.env['hr.analytic.timesheet']
                    prj_obj = self.env['project.project']
                    project = prj_obj.browse([project_id])
                    account_id = project.analytic_account_id.id
                    unit_amount = duration
                    company_time_unit_id = self.env['res.users'].browse([user_id]).company_id.project_time_mode_id.id
                    employee_time_unit_id = ts_obj._getEmployeeUnit(context={'user_id': user_id})
                    # If the company has a different time unit than the employee we need to recalculate unit_amount
                    if company_time_unit_id != employee_time_unit_id:
                        unit_amount = self.env['product.uom']._compute_qty(company_time_unit_id,
                                                                           unit_amount,
                                                                           employee_time_unit_id)
                    ts_values = {
                        'name': worklog_text or name,
                        'user_id': user_id,
                        'date': start,
                        'unit_amount': unit_amount,
                        'account_id': account_id,
                        'journal_id': ts_obj._getAnalyticJournal(context={'user_id': user_id}),
                        'product_id': ts_obj._getEmployeeProduct(context={'user_id': user_id}),
                        'product_uom_id': employee_time_unit_id,
                        'general_account_id': ts_obj._getGeneralAccount(context={'user_id': user_id}),
                        'event_category_id': category_id,
                    }
                    # Update an existing project worklog
                    # HINT: If the project changed the project worklog would already be deleted
                    #       So an update id only possible if the project exists and stayed the same.
                    if self.analytic_time_id:
                        self.analytic_time_id.write(ts_values)
                    # Create a project worklog
                    # HINT: We did not write the event so need to create the worklog without self.analytic_time_id
                    else:
                        project_worklog = ts_obj.create(ts_values)
                        values['analytic_time_id'] = project_worklog.id

            # ==========
            # ATTENDANCE
            # ==========
            # Unlink attendance
            if not is_attendance:
                if self.sign_in_id:
                    self.sign_in_id.unlink()
                if self.sign_out_id:
                    self.sign_out_id.unlink()

            # Create or Update Attendance
            if is_attendance:
                attendance_obj = self.env['hr.attendance']
                # Get the employee id
                employee_obj = self.env['hr.employee']
                employee_id = employee_obj.search([('user_id', '=', self.user_id.id)], limit=1).id
                assert employee_id, _('No employee found for current user!')

                # SIGN_IN attendance
                sign_in_values = {
                    'employee_id': employee_id,
                    'name': start,
                    'action': 'sign_in',
                }
                # Update existing sign-in attendance
                if self.sign_in_id:
                    self.sign_in_id.write(sign_in_values)
                # Create new sign-in attendance
                else:
                    sign_in = attendance_obj.create(sign_in_values)
                    values['sign_in_id'] = sign_in.id

                # SIGN_OUT attendance
                sign_out_values = {
                    'employee_id': employee_id,
                    'name': stop,
                    'action': 'sign_out',
                }
                # Update existing sign-out attendance
                if self.sign_out_id:
                    self.sign_out_id.write(sign_out_values)
                # Create new sign-out attendance
                else:
                    sign_out = attendance_obj.create(sign_out_values)
                    values['sign_out_id'] = sign_out.id

        return super(calendar_event, self).write(values)

    @api.multi
    def unlink(self):
        for event in self:
            if event.task_work_id:
                event.task_work_id.unlink()
            if event.analytic_time_id:
                event.analytic_time_id.unlink()
            if event.sign_in_id:
                event.sign_in_id.unlink()
            if event.sign_out_id:
                event.sign_out_id.unlink()
        return super(calendar_event, self).unlink()


class hr_timesheet_sheet_sheet_day_cat_detail(osv.osv):
    _name = "hr_timesheet_sheet.sheet.day_cat_detail"
    _description = "Category by Days in Period"
    _auto = False
    _order = 'name'

    # Fields:
    name = Date(string='Date', readonly='True')
    timesheet_id = Many2one(comodel_name='hr_timesheet_sheet.sheet', string='Timesheet')
    employee_id = Many2one(comodel_name='hr.employee', string='Employee')

    ga = Float(string="GA", readonly='True')
    ga_e = Float(string="GA Expense", readonly='True')
    ga_a = Float(string="GA Abroad", readonly='True')
    ga_ae = Float(string="GA Abroad Expense", readonly='True')

    cm = Float(string="CM", readonly='True')
    cm_e = Float(string="CM Expense", readonly='True')
    cm_a = Float(string="CM Abroad", readonly='True')
    cm_ae = Float(string="CM Abroad Expense", readonly='True')

    t = Float(string="T", readonly='True')
    t_e = Float(string="T Expense", readonly='True')
    t_a = Float(string="T Abroad", readonly='True')
    t_ae = Float(string="T Abroad Expense", readonly='True')

    os = Float(string="OS", readonly='True')
    os_e = Float(string="OS Expense", readonly='True')
    os_a = Float(string="OS Abroad", readonly='True')
    os_ae = Float(string="OS Abroad Expense", readonly='True')

    sum_e = Float(string="Expense", readonly='True')
    sum_a = Float(string="Abroad", readonly='True')
    sum_ae = Float(string="Abroad Expense", readonly='True')

    # Sum of the events categories per day
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_timesheet_sheet_sheet_day_cat_detail')
        cr.execute(""" CREATE OR REPLACE VIEW hr_timesheet_sheet_sheet_day_cat_detail as (
            select
                 cast((cast(ts.id AS BIGINT) * 100000 + ((period.day::date - ts.date_from::timestamp::date) + 1)) AS BIGINT) AS id
                ,cast(ts.id AS BIGINT) AS timesheet_id
                ,cast(ts.employee_id AS BIGINT)
                ,cast(ts.user_id AS BIGINT)
                ,period.day as name
                ,count(distinct e.id)
                ,sum(case when cc.name = 'GENERAL ACTIVITY' then e.duration else 0 end) ga
                ,sum(case when cc.name = 'GENERAL ACTIVITY > Expense Entitled' then e.duration else 0 end) ga_e
                ,sum(case when cc.name = 'GENERAL ACTIVITY > Abroad' then e.duration else 0 end) ga_a
                ,sum(case when cc.name = 'GENERAL ACTIVITY > Abroad > Expense Entitled' then e.duration else 0 end) ga_ae
                ,sum(case when cc.name = 'CUSTOMER MEETING' then e.duration else 0 end) cm
                ,sum(case when cc.name = 'CUSTOMER MEETING > Expense Entitled' then e.duration else 0 end) cm_e
                ,sum(case when cc.name = 'CUSTOMER MEETING > Abroad' then e.duration else 0 end) cm_a
                ,sum(case when cc.name = 'CUSTOMER MEETING > Abroad > Expense Entitled' then e.duration else 0 end) cm_ae
                ,sum(case when cc.name = 'TRIP' then e.duration else 0 end) t
                ,sum(case when cc.name = 'TRIP > Expense Entitled' then e.duration else 0 end) t_e
                ,sum(case when cc.name = 'TRIP > Abroad' then e.duration else 0 end) t_a
                ,sum(case when cc.name = 'TRIP > Abroad > Expense Entitled' then e.duration else 0 end) t_ae
                ,sum(case when cc.name = 'OVERNIGHT STAY > Expense Entitled' then e.duration else 0 end) os_e
                ,sum(case when cc.name = 'OVERNIGHT STAY > Abroad' then e.duration else 0 end) os_a
                ,sum(case when cc.name = 'OVERNIGHT STAY > Abroad > Expense Entitled' then e.duration else 0 end) os_ae
                ,sum(case when cc.name = 'OVERNIGHT STAY' then e.duration else 0 end) os
                -- ,sum(case when cc.name like '%Expense%' then e.duration else 0 end) sum_exp
                -- ,sum(case when cc.name like '%Abroad%' then e.duration else 0 end) sum_abr
                ,sum(case when cc.name in ( 'GENERAL ACTIVITY > Expense Entitled'
                                           ,'CUSTOMER MEETING > Expense Entitled'
                                           ,'TRIP > Expense Entitled'
                                            ) then e.duration else 0 end) sum_e
                ,sum(case when cc.name in ( 'GENERAL ACTIVITY > Abroad'
                                           ,'CUSTOMER MEETING > Abroad'
                                           ,'TRIP > Abroad'
                                            ) then e.duration else 0 end) sum_a
                ,sum(case when cc.name in ( 'GENERAL ACTIVITY > Abroad > Expense Entitled'
                                           ,'CUSTOMER MEETING > Abroad > Expense Entitled'
                                           ,'TRIP > Abroad > Expense Entitled'
                                            ) then e.duration else 0 end) sum_ae
                ,p.name partner_name
            from   hr_timesheet_sheet_sheet ts
            inner join res_users u
                on u.id = ts.user_id
            inner join res_partner p
                on p.id = u.partner_id
            cross join generate_series(ts.date_from::timestamp without time zone, ts.date_to::timestamp without time zone, '1 day'::interval) period(day)
            left join calendar_event e
                on e.user_id = ts.user_id
                   and e.start_datetime::timestamp::date = period.day::timestamp::date
                   and e.category_id in (select id from calendar_event_category where name in
                                                        ('GENERAL ACTIVITY'
                                                        ,'GENERAL ACTIVITY > Expense Entitled'
                                                        ,'GENERAL ACTIVITY > Abroad'
                                                        ,'GENERAL ACTIVITY > Abroad > Expense Entitled'
                                                        ,'CUSTOMER MEETING'
                                                        ,'CUSTOMER MEETING > Expense Entitled'
                                                        ,'CUSTOMER MEETING > Abroad'
                                                        ,'CUSTOMER MEETING > Abroad > Expense Entitled'
                                                        ,'TRIP'
                                                        ,'TRIP > Expense Entitled'
                                                        ,'TRIP > Abroad'
                                                        ,'TRIP > Abroad > Expense Entitled'
                                                        ,'OVERNIGHT STAY > Expense Entitled'
                                                        ,'OVERNIGHT STAY > Abroad'
                                                        ,'OVERNIGHT STAY > Abroad > Expense Entitled'
                                                        ,'OVERNIGHT STAY'))

            left join calendar_event_category cc
                on cc.id = e.category_id
            group by
                 ts.id
                ,ts.employee_id
                ,ts.user_id
                ,period.day
                ,p.name
            order by ts.id, period.day
            )""")


class hr_timesheet_sheet(osv.osv):
    _inherit = 'hr_timesheet_sheet.sheet'

    day_cat_details = One2many(comodel_name='hr_timesheet_sheet.sheet.day_cat_detail',
                               inverse_name='timesheet_id',
                               string='Day Cat Details',
                               readonly='True')

