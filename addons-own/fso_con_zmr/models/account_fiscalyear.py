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
    @api.constrains('date_start', 'date_end', 'ze_datum_von', 'ze_datum_bis',
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
                        raise ValidationError(_("Fiscal year date_end and ze_datum_bis differ more than 30 days!"))

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
                logger.warning("compute_meldungs_jahr(): Suspicious number of days: %s" % time_range.days)
                y.meldungs_jahr = False
                continue

            # Find the year in the date range with the most time
            years_in_range = range(date_start.year, date_stop.year + 1)
            if len(years_in_range) == 1:
                y.meldungs_jahr = str(years_in_range[0])
                continue

            # Calculate delta from date_start to end of year
            date_start_end_of_year = datetime.datetime(date_start.year, 12, 31, 23, 59, 59)
            date_start_range = date_start_end_of_year - date_start

            # Calculate delta from start of year to date_stop
            date_stop_start_of_year = datetime.datetime(date_stop.year, 1, 1, 0, 0)
            date_stop_range = date_stop - date_stop_start_of_year

            y_range = date_start_range if date_start_range > date_stop_range else date_stop_range
            if not check_range(y_range.days):
                logger.warning("compute_meldungs_jahr(): Suspicious number of days for meldejahr: %s" % y_range.days)
                y.meldungs_jahr = False
                continue

            y.meldungs_jahr = date_start.year if date_start_range > date_stop_range else date_stop.year
