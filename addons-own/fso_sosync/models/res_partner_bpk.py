# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner.bpk"
    _inherit = ["res.partner.bpk", "base.sosync"]


    # FIELDS
    # res.company
    BPKRequestCompanyID = fields.Many2one(sosync="True")

    # res.partner
    BPKRequestPartnerID = fields.Many2one(sosync="True")

    # To make sorting the BPK request easier
    LastBPKRequest = fields.Datetime(sosync="True")

    # Make debugging of multiple request on error easier
    BPKRequestLog = fields.Text(sosync="True")

    # Successful BPK request field set
    # --------------------------------
    # This set of fields gets only updated if private and public bpk was returned successfully
    BPKPrivate = fields.Char(sosync="True")
    BPKPublic = fields.Char(sosync="True")

    BPKRequestDate = fields.Datetime(sosync="True")
    BPKRequestURL = fields.Char(sosync="True")
    BPKRequestData = fields.Text(sosync="True")
    BPKRequestFirstname = fields.Char(sosync="True")
    BPKRequestLastname = fields.Char(sosync="True")
    BPKRequestBirthdate = fields.Date(sosync="True")
    BPKRequestZIP = fields.Char(sosync="True")

    BPKResponseData = fields.Text(sosync="True")
    BPKResponseTime = fields.Float(sosync="True")

    # Invalid BPK request field set
    # -----------------------------
    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    BPKErrorCode = fields.Char(sosync="True")
    BPKErrorText = fields.Text(sosync="True")

    BPKErrorRequestDate = fields.Datetime(sosync="True")
    BPKErrorRequestURL = fields.Char(sosync="True")
    BPKErrorRequestData = fields.Text(sosync="True")
    BPKErrorRequestFirstname = fields.Char(sosync="True")
    BPKErrorRequestLastname = fields.Char(sosync="True")
    BPKErrorRequestBirthdate = fields.Date(sosync="True")
    BPKErrorRequestZIP = fields.Char(sosync="True")

    BPKErrorResponseData = fields.Text(sosync="True")
    BPKErrorResponseTime = fields.Float(sosync="True")
