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
    drg_last = fields.Datetime(string="Last Donation Report Generation", readonly=True,
                               help="Last Donation Report Generation in FRST.")

    # TODO: Add some validation (fiscal year must match meldezeitraum_start etc.)