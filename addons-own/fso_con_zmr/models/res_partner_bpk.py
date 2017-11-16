# -*- coding: utf-8 -*-
from openerp import api, models, fields
import logging
import time
import datetime
from dateutil import parser as du_parser
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class ResPartnerBPK(models.Model):
    _name = 'res.partner.bpk'

    # ------
    # FIELDS
    # ------
    # res.company
    BPKRequestCompanyID = fields.Many2one(comodel_name='res.company', string="BPK Request Company",
                                          required=True, readonly=True)

    # res.partner
    BPKRequestPartnerID = fields.Many2one(comodel_name='res.partner', string="BPK Request Partner",
                                          required=True, readonly=True)

    # res.partner.fa_donation_report
    fa_donation_report_ids = fields.One2many(comodel_name="res.partner.fa_donation_report",
                                             inverse_name="sub_bpk_id",
                                             string="Donation Reports")

    # To make sorting the BPK request easier
    LastBPKRequest = fields.Datetime(string="Last BPK Request", readonly=True)

    # Make debugging of multiple request on error easier
    BPKRequestLog = fields.Text(string="Request Log", readonly=True)

    # ATTENTION: If you change this field don't forget to change bpk_id_state field in res_partner.py also!
    state = fields.Selection(selection=[('found', 'Found'),
                                        ('found_old', 'Found with old data'),
                                        ('error', 'Error')],
                             string="State", readonly=True)

    # Successful BPK request field set
    # --------------------------------
    # This set of fields gets only updated if private and public bpk was returned successfully
    BPKPrivate = fields.Char(string="BPK Private", readonly=True)
    BPKPublic = fields.Char(string="BPK Public", readonly=True)

    BPKRequestDate = fields.Datetime(string="BPK Request Date", readonly=True)
    BPKRequestURL = fields.Char(string="BPK Request URL", readonly=True)
    BPKRequestData = fields.Text(string="BPK Request Data", readonly=True)
    BPKRequestFirstname = fields.Char(string="BPK Request Firstname", readonly=True)
    BPKRequestLastname = fields.Char(string="BPK Request Lastname", readonly=True)
    BPKRequestBirthdate = fields.Date(string="BPK Request Birthdate", readonly=True)
    BPKRequestZIP = fields.Char(string="BPK Request ZIP", readonly=True)

    BPKResponseData = fields.Text(string="BPK Response Data", readonly=True)
    BPKResponseTime = fields.Float(string="BPK Response Time", readonly=True)

    BPKRequestVersion = fields.Integer(string="BPK Request Version", readonly=True)

    # Invalid BPK request field set
    # -----------------------------
    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    BPKErrorCode = fields.Char(string="BPK-Error Code", readonly=True)
    BPKErrorText = fields.Text(string="BPK-Error Text", readonly=True)

    BPKErrorRequestDate = fields.Datetime(string="BPK-Error Request Date", readonly=True)
    BPKErrorRequestURL = fields.Char(string="BPK-Error Request URL", readonly=True)
    BPKErrorRequestData = fields.Text(string="BPK-Error Request Data", readonly=True)
    BPKErrorRequestFirstname = fields.Char(string="BPK-Error Request Firstname", readonly=True)
    BPKErrorRequestLastname = fields.Char(string="BPK-Error Request Lastname", readonly=True)
    BPKErrorRequestBirthdate = fields.Date(string="BPK-Error Request Birthdate", readonly=True)
    BPKErrorRequestZIP = fields.Char(string="BPK-Error Request ZIP", readonly=True)

    BPKErrorResponseData = fields.Text(string="BPK-Error Response Data", readonly=True)
    BPKErrorResponseTime = fields.Float(string="BPK-Error Response Time", readonly=True)

    BPKErrorRequestVersion = fields.Integer(string="BPK-Error Request Version", readonly=True)

    # -------------
    # MODEL ACTIONS
    # -------------
    @api.model
    def _compute_state(self, BPKRequestDate, BPKErrorRequestDate):
        if BPKRequestDate and not isinstance(BPKRequestDate, datetime.datetime):
            BPKRequestDate = du_parser.parse(BPKRequestDate)
            logger.debug("_compute_state() BPKRequestDate is not a datetime object for %s", self.ids)
        if BPKErrorRequestDate and not isinstance(BPKErrorRequestDate, datetime.datetime):
            BPKErrorRequestDate = du_parser.parse(BPKErrorRequestDate)
            logger.debug("_compute_state() BPKRequestDate is not a datetime object for %s", self.ids)
        state = None
        if not BPKRequestDate and not BPKErrorRequestDate:
            state = None
        elif BPKRequestDate and not BPKErrorRequestDate:
            state = 'found'
        elif BPKErrorRequestDate and not BPKRequestDate:
            state = 'error'
        elif BPKRequestDate >= BPKErrorRequestDate:
            state = 'found'
        elif BPKRequestDate < BPKErrorRequestDate:
            state = 'found_old'
        return state

    # --------------
    # RECORD ACTIONS
    # --------------
    @api.model
    def create(self, vals):
        # Compute State
        BPKRequestDate = vals.get('BPKRequestDate')
        BPKErrorRequestDate = vals.get('BPKErrorRequestDate')
        state = self._compute_state(BPKRequestDate, BPKErrorRequestDate)
        vals.update({'state': state})
        return super(ResPartnerBPK, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(ResPartnerBPK, self).write(vals)
        if res:
            for r in self:
                BPKRequestDate = vals.get('BPKRequestDate') or r.BPKRequestDate
                BPKErrorRequestDate = vals.get('BPKErrorRequestDate') or r.BPKErrorRequestDate
                computed_state = self._compute_state(BPKRequestDate, BPKErrorRequestDate)
                if r.state != computed_state:
                    r.write({'state': computed_state})
        return res

    # --------------
    # BUTTON ACTIONS
    # --------------
    @api.multi
    def compute_state(self):
        self.write({})

    # ----------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED PROCESSING
    # ----------------------------------------
    @api.model
    def scheduled_compute_state(self):
        start = time.time()

        # SET LIMIT
        # HINT: We estimate the fastest speed with 10ms per record (Speed on macbook was 16ms)
        interval_to_seconds = {
            "weeks": 7 * 24 * 60 * 60,
            "days": 24 * 60 * 60,
            "hours": 60 * 60,
            "minutes": 60,
            "seconds": 1
        }
        scheduled_action = self.env.ref('fso_con_zmr.ir_cron_scheduled_compute_state')
        max_runtime_sec = int(scheduled_action.interval_number *
                              interval_to_seconds[scheduled_action.interval_type])
        limit = int((max_runtime_sec * 1000) / 10)

        # GET RECORDS
        bpk_state_missing = self.search(['&',
                                         ('state', '=', False),
                                         '|',
                                           ('BPKRequestDate', '!=', False),
                                           ('BPKErrorRequestDate', '!=', False)],
                                        limit=limit)
        # If limit is not yet reached append records where the state must be unset
        remaining_slots = limit-len(bpk_state_missing)
        if remaining_slots:
            bpk_state_set_wrong = self.search([('state', '!=', False),
                                               ('BPKRequestDate', '=', False),
                                               ('BPKErrorRequestDate', '=', False)],
                                              limit=remaining_slots)
        records = bpk_state_missing | bpk_state_set_wrong

        # PROCESS RECORDS
        logger.info("scheduled_compute_state() compute state for %s res.partner.bpk" % len(records))
        runtime_end = datetime.datetime.now() + datetime.timedelta(0, max_runtime_sec - int(time.time() - start) - 10)
        for r in records:
            # Check remaining runtime
            if datetime.datetime.now() >= runtime_end:
                break
            # recalculate the state
            r.write({})
