# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _

import os
from os.path import join as pj
import logging
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


# Austrian Finanzamt Donation Reports (Spendenmeldung)
class ResPartnerFADonationReport(models.Model):
    _name = 'res.partner.fa_donation_report'

    # FIELDS
    # Donation Report FA (=Spendenmeldung fuer das Finanzamt Oesterreich)
    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner",
                                 required=True, readonly=True)
    bpk_company_id = fields.Many2one(comodel_name='res.company', string="BPK Company",
                                     required=True, readonly=True)
    anlage_am_um = fields.Datetime(string="Donation Report Date", required=True, readonly=True)
    ze_datum_von = fields.Datetime(string="Donation Report Start", required=True, readonly=True)
    ze_datum_bis = fields.Datetime(string="Donation Report End", required=True, readonly=True)
    meldungs_jahr = fields.Integer(string="Donation Report Year", required=True, readonly=True)
    betrag = fields.Float(string="Donation Report Sum", required=True, readonly=True)

    # Submission Information
    sub_datetime = fields.Datetime(string="Submission Date", readonly=True)
    sub_url = fields.Char(string="Submission URL", readonly=True)
    # HINT: This is set by FS-Online at submission!
    sub_typ = fields.Selection(string="Donation Report Type", readonly=True,
                               selection=[('E', 'Erstuebermittlung'),
                                          ('A', 'Aenderungsuebermittlung'),
                                          ('S', 'Stornouebermittlung')])
    sub_mode = fields.Selection(string="Spendenmeldung Modus", readonly=True,
                                selection=[('T', 'Testumgebung'),
                                           ('P', 'Echtbetrieb')])
    sub_data = fields.Char(string="Submission Data", readonly=True)
    sub_response = fields.Char(string="Response", readonly=True)
    sub_request_time = fields.Float(string="Request Time", readonly=True)
    sub_log = fields.Text(string="Submission Log", readonly=True)
    # Submission BPK Information (Gathered at submission time from res.partner.bpk and copied here)
    sub_bpk_id = fields.Many2one(comodel_name='res.partner.bpk', string="BPK Request", readonly=True)
    sub_bpk_company_name = fields.Char(string="BPK Company Name", readonly=True)
    sub_bpk_company_stammzahl = fields.Char(string="BPK Company Stammzahl", readonly=True)
    sub_bpk_private = fields.Char(string="BPK Private", readonly=True)
    sub_bpk_public = fields.Char(string="BPK Public", readonly=True)
    sub_bpk_firstname = fields.Char(string="BPK Firstname", readonly=True)
    sub_bpk_lastname = fields.Char(string="BPK Lastname", readonly=True)
    sub_bpk_birthdate = fields.Date(string="BPK Birthdate", readonly=True)
    sub_bpk_zip = fields.Char(string="BPK ZIP", readonly=True)

    # Error Information
    error_code = fields.Char(string="Error Code", readonly=True)
    error_text = fields.Char(string="Error Information", readonly=True)

    # State Information
    skipped_by_id = fields.Many2one(comodel_name='res.partner.fa_donation_report',
                                    string="Skipped by",
                                    readonly=True)
    skipped = fields.One2many(comodel_name="res.partner.fa_donation_report",
                              inverse_name="skipped_by_id",
                              string="Skipped", readonly=True)
    state = fields.Selection(string="State", selection=[('new', 'New'),
                                                        ('approved', 'Approved'),
                                                        ('skipped', 'Skipped'),
                                                        ('submitted', 'Submitted'),
                                                        ('error', 'Error')],
                             default='new',
                             readonly=True)

    @api.multi
    def submit_donation_report_to_fa(self):
        # LOGIN TO FINANZ ONLINE

        # SUBMIT DONATION REPORT(S) (Spendenmeldung)
        for report in self:

            # TODO: Check donation_deduction_optout and donation_deduction_disabled

            # TODO: Check report state (skip all donation reports where state is not "approved" or "error")

            # TODO: Login to Finanz Online
            #       HINT: todo: the login method MUST CHECK IF THE SESSION ID IS STILL VALID

            # TODO: Find the correct "Uebermittlungs_Typ"
            # E = Erstmeldung (if there are no other submissions for this person for this meldungs_jahr)
            # A = Aenderung (if there are already send reports for this person with the same meldungs_jahr)
            #     !!!Ohne vbPK!!! ABER RefNr = RefNr der Erstmeldung!
            # S = Stornierung ( if the "betrag" is 0 or negative and there is a send report of type E or A
            #                   for this meldungs_jahr)
            #     !!!Ohne vbPK UND ohne Betrag!!! ABER RefNr = RefNr der Erstmeldung!
            #
            # HINT: If the Uebermittlungs_Typ is S but there are no other already send reports for this year we
            #       will not send anything but simply skipp the not send reports and this one to so nothing was send
            #       at all
            #       TODO: Check if a many2one and one2many can point to itself

            # HINT: RefNr must be the id in the "partner_id" field

            # TODO: Send Data (FileUpload) To Finanz Online
            #       HINT: In case of an error retry to "Login to Finanz Online"

            # TODO: Update the donation report record

        # TODO: Logout all companies from Finanz Online

    #
    # TODO: Add scheduler action and scheduler xml-data-record
    #
