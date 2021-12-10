# -*- coding: utf-'8' "-*-"
from openerp import models, api
import logging
_logger = logging.getLogger(__name__)


class HRTimesheetSheetSheet(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'

    @api.multi
    def _total_sums(self, field_name=None, arg=None):
        _logger.info("_total_sums(), field_name: %s, arg: %s" % (field_name, arg))
        # Make sure all entries created by calendar events are correct
        cal_obj = self.env['calendar.event']
        for sheet in self:
            # HINT: used start_date twice instead of end_date to catch overday events
            events_to_update = cal_obj.search([('user_id', '=', sheet.user_id.id),
                                               ('start', '!=', False),
                                               ('stop', '!=', False),
                                               ('start', '>=', sheet.date_from + ' 00:00:00'),
                                               ('stop', '<=', sheet.date_to + ' 23:59:59'),
                                               ])
            _logger.info("_total_sums() found %s calendar events in this timesheet range" % len(events_to_update))

            for event in events_to_update:
                vals = {}

                # CLEANUP: Remove worklog if not linked to a project
                if event.is_worklog and not event.project_id:
                    vals['is_worklog'] = False

                # CLEANUP: Make sure the partner of the user is also a participant
                if event.is_worklog or event.is_attendance:
                    if event.user_id and event.user_id.partner_id not in event.partner_ids:
                        _logger.warning("Calender event %s found with worklog and/or attendance set but "
                                        "without user_id.partner_id in participants!" % event.id)
                        vals['partner_ids'] = [(4, event.user_id.partner_id.id, '')]

                # UPDATE: write event to recalculate attendance and worklog records and set CLEANUP values if any
                event.write(vals)

            _logger.info("_total_sums() all calendar event related work-log and attendance records updated")

        return super(HRTimesheetSheetSheet, self)._total_sums(field_name=field_name, arg=arg)

    @api.multi
    def button_compute_all(self):
        """ Recompute values for all open timesheets
        :return: bool
        """

        # Find all timesheets for the users of selected timesheets in state draft and order them by date_from ascending
        users = self.mapped('user_id')
        timesheets = self.search([('user_id', 'in', users.ids), ('state', '=', 'draft')],
                                 order="user_id, date_from")

        # Recalculate
        for sheet in timesheets:
            sheet.button_compute()

        return True

    @api.multi
    def button_compute_all_users(self):
        timesheets = self.search([('state', '=', 'draft')],
                                 order="date_from")

        users_log = ', '.join([str(sheet.user_id.id) for sheet in timesheets])
        _logger.debug("Calculating open time sheets for users: %s" % users_log)

        # Recalculate
        for sheet in timesheets:
            sheet.button_compute()

        return True
