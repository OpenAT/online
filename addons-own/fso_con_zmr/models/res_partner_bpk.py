# -*- coding: utf-8 -*-
from openerp import api, models, fields
import logging
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class ResPartnerBPK(models.Model):
    _name = 'res.partner.bpk'

    # FIELDS
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
