# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields


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

    # TODO: Add some validation (fiscal year must match meldezeitraum_start etc.)
