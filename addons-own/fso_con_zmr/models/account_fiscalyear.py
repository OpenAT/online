# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import ValidationError

import datetime
import logging
logger = logging.getLogger(__name__)


# addon account (already in fso_base)
class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscalyear'

    # ------
    # FIELDS
    # ------

    # Betrachtungszeitraum
    ze_datum_von = fields.Datetime(string="Betrachtungszeitraum Start",
                                   help="Include donations starting with this date and time")
    ze_datum_bis = fields.Datetime(string="Betrachtungszeitraum Ende",
                                   help="Include donations starting up to and including this date and time")

    # Set by the FRST account manager e.g.: Marcus
    meldezeitraum_start = fields.Datetime(string="Meldezeitraum Start",
                                          help="Scheduled Donation Report Submission Start")
    meldezeitraum_end = fields.Datetime(string="Meldezeitraum Ende",
                                        help="Scheduled Donation Report Submission End")

    # HINT: drg = Donation Report Generation
    drg_interval_number = fields.Integer(string="Donation Report Generation Interval",
                                         help="Repeat every X.")
    drg_interval_type = fields.Selection(string="Donation Report Generation Interval Type",
                                         selection=[#('minutes', 'Minutes'),
                                                    #('hours', 'Hours'),
                                                    #('work_days', 'Work Days'),
                                                    ('days', 'Days'),
                                                    #('weeks', 'Weeks'),
                                                    ('months', 'Months')
                                         ])

    drg_next_run = fields.Datetime(string="Next Scheduled DRG in FRST", readonly=True,
                                   help="Next scheduled run for donation report checks/generation STP in FRST")

    drg_last = fields.Datetime(string="Last DRG in FRST", readonly=True,
                               help="Last scheduled run of the donation report checks/generation STP in FRST")
    drg_last_count = fields.Integer(string="Number of Rep. for last DRG", readonly=True,
                                    help="Number of Donation Report(s) generated at the last scheduled run in FRST")

    # # TODO: WORK IN PROGRESS compute meldejahr
    meldungs_jahr = fields.Char(string="Meldejahr", readonly=True, compute="compute_meldungs_jahr", store=True,
                                help="computed by ze_datum_von and ze_datum_bis")

    # ---------------
    # API CONSTRAINTS
    # ---------------
    @api.constrains('date_start', 'date_stop', 'ze_datum_von', 'ze_datum_bis',
                    'meldezeitraum_start', 'meldezeitraum_end')
    def _constrain_donation_report_dates(self):

        def str_to_datetime(time_str=''):
            if not time_str:
                return time_str
            try:
                return datetime.datetime.strptime(time_str, DEFAULT_SERVER_DATETIME_FORMAT)
            except:
                try:
                    return datetime.datetime.strptime(time_str, DEFAULT_SERVER_DATE_FORMAT)
                except:
                    return False

        for r in self:
            # Convert strings to datetimes
            date_start = str_to_datetime(r.date_start)
            date_stop = str_to_datetime(r.date_stop)
            ze_datum_von = str_to_datetime(r.ze_datum_von)
            ze_datum_bis = str_to_datetime(r.ze_datum_bis)
            meldezeitraum_start = str_to_datetime(r.meldezeitraum_start)
            meldezeitraum_end = str_to_datetime(r.meldezeitraum_end)

            # Check "Betrachtungszeitraum"
            if ze_datum_von or ze_datum_bis:
                # Check both fields are set
                if not (ze_datum_von and ze_datum_bis):
                    raise ValidationError(_("Fields ze_datum_von and ze_datum_bis must be set if one of them is set!"))
                ze_range = ze_datum_bis - ze_datum_von
                # Check range
                if ze_datum_von > ze_datum_bis:
                    raise ValidationError(_("ze_datum_bis before ze_datum_von!"))
                if not bool(((365 + 20) > ze_range.days > (365 - 20))):
                    raise ValidationError(_(
                        "Number of days between ze_datum_von and ze_datum_bis must be between 345-385 but is %s"
                        "") % ze_range.days)
                # Check year
                if ze_datum_von.year < 2016:
                    raise ValidationError(_("'ze_datum_von' year must be 2016 or up!"))
                # Check Betrachtungszeitraum start against fiscal year start
                if date_start:
                    ze_start_range = date_start - ze_datum_von
                    if abs(ze_start_range.days) > 30:
                        raise ValidationError(_("Fiscal year start_date and ze_datum_von differ more than 30 days!"))
                # Check Betrachtungszeitraum end against fiscal year end
                if date_stop:
                    ze_end_range = date_stop - ze_datum_bis
                    if abs(ze_end_range.days) > 30:
                        raise ValidationError(_("Fiscal year date_stop and ze_datum_bis differ more than 30 days!"))

            # Check Meldezeitraum
            if meldezeitraum_start or meldezeitraum_end:
                # Check both fields are set
                if not (meldezeitraum_start and meldezeitraum_end):
                    raise ValidationError(_(
                        "Fields meldezeitraum_start and meldezeitraum_end must be set if one of them is set!"))
                # Check range
                if meldezeitraum_end < meldezeitraum_start:
                    raise ValidationError(_("meldezeitraum_end before meldezeitraum_start!"))
                mz_range = meldezeitraum_end - meldezeitraum_start
                if mz_range.days > (5*365):
                    raise ValidationError(_("Meldezeitraum range can not be more than 5 years!"))
                # Check against Betrachtungszeitraum
                if ze_datum_bis > meldezeitraum_start:
                    raise ValidationError(_("Meldezeitraum starts inside/before Betrachtungszeitraum!"))
                ze_mz_range = meldezeitraum_start - ze_datum_bis
                if abs(ze_mz_range.days) > (4*30):
                    raise ValidationError(_("Meldezeitraum starts more than 4 Months after the Betrachtungszeitraum!"))

    # ---------------
    # COMPUTED FIELDS
    # ---------------

    @api.depends('ze_datum_von', 'ze_datum_bis',)
    def compute_meldungs_jahr(self):

        def check_range(days):
            days = int(days)
            return bool(((365 + 20) > days > (365 - 20)))

        for y in self:
            if not y.ze_datum_von or not y.ze_datum_bis:
                y.meldungs_jahr = False
                continue

            # Datetime objects from strings (Betrachtungszeitraum)
            date_start = datetime.datetime.strptime(y.ze_datum_von, DEFAULT_SERVER_DATETIME_FORMAT)
            date_stop = datetime.datetime.strptime(y.ze_datum_bis, DEFAULT_SERVER_DATETIME_FORMAT)

            # Check time range
            time_range = date_stop - date_start
            if not check_range(time_range.days):
                logger.warning("compute_meldungs_jahr(): Suspicious number of days for Betrachtungszeitraum: %s"
                               "" % time_range.days)
                y.meldungs_jahr = False
                continue

            # Compute meldungs_jahr based on Betrachtungszeitraum
            # ---
            # HINT: since range would not include the "Target/Max" value we have to use +1
            years_in_range = range(date_start.year, date_stop.year + 1)
            start = date_start
            end = date_stop + datetime.timedelta(1)

            # Find the year in the date range with the most days
            max_year = {'year': 0, 'days': 0}
            for year in years_in_range:
                year_start = datetime.datetime(year, 1, 1, 0, 0)
                year_end = datetime.datetime(year + 1, 1, 1, 0, 0)

                days_in_year = min(end, year_end) - max(start, year_start)
                days_in_year = days_in_year.days

                if int(max_year['days']) < int(days_in_year):
                    max_year = {'year': year, 'days': days_in_year}

            # Update meldungs_jahr
            if check_range(max_year['days']):
                y.meldungs_jahr = str(max_year['year'])
            else:
                logger.warning("compute_meldungs_jahr(): Suspicious number of days for Meldejahr: %s"
                               "" % max_year['days'])
                y.meldungs_jahr = False
