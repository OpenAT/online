# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.soap import soap_request

from lxml import etree
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
    # HINT: This is set by FS-Online at submission!
    sub_datetime = fields.Datetime(string="Submission Date", readonly=True)
    sub_url = fields.Char(string="Submission URL", readonly=True)

    sub_typ = fields.Selection(string="Donation Report Type", readonly=True,
                               selection=[('E', 'Erstuebermittlung'),
                                          ('A', 'Aenderungsuebermittlung'),
                                          ('S', 'Stornouebermittlung')])
    sub_data = fields.Char(string="Submission Data", readonly=True)
    sub_response = fields.Char(string="Response", readonly=True)
    sub_request_time = fields.Float(string="Request Time", readonly=True)
    sub_log = fields.Text(string="Submission Log", readonly=True)
    # Reference Number (Only for Submission with sub_typ E)
    sub_refnr = fields.Char(string="Reference Number", readonly=True,
                            help=_("Die RefNr muss pro Jahr, Uebermittlungsart und Uebermittler "
                                   "eindeutig sein."))
    sub_erstmeldung_id = fields.Many2one(comodel_name='res.partner.fa_donation_report',
                                         string="Erstmeldung", readonly=True)
    sub_follow_up_ids = fields.One2many(comodel_name="res.partner.fa_donation_report",
                              inverse_name="sub_erstmeldung_id",
                              string="Follow-Up Reports", readonly=True)
    # BPK Company Settings (Gathered at submission time from res.company and copied here)
    sub_company_mode = fields.Char(string="Spendenmeldung Modus", readonly=True)
    sub_company_type = fields.Char(string="Spendenmeldung Uebermitllungstyp", readonly=True)
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
                                                        ('error', 'Error'),
                                                        ('exception', 'Exception')],
                             default='new',
                             readonly=True)

    @api.multi
    def _find_bpk_record(self):
        assert self.ensure_one(), _("_find_bpk_record() works only for a single record!")
        bpk_obj = self.env['res.partner.bpk']
        bpk_record = bpk_obj.search([('BPKRequestCompanyID', '=', self.bpk_company_id),
                                     ('BPKRequestPartnerID', '=', self.partner_id)])
        assert len(bpk_record) == 1, _("None or multiple BPK records where found for partner %s %s with company %s %s! "
                                       "(bpk record ids: )") % (self.partner_id.id, self.partner_id.name,
                                                                self.bpk_company_id.id, self.bpk_company_id.name,
                                                                bpk_record.ids or '')
        return bpk_record

    @api.multi
    def _donation_report_update(self, state=str(), response=None, bpk=None, **kwargs):
        assert self.ensure_one(), _("_donation_report_update() works only for a single record!")
        assert state, _("Required keyword argument 'state' is missing!")

        values = {
            # State
            'state': state,

            # Submission information
            'sub_datetime': kwargs.get('sub_datetime') or fields.datetime.now(),
            'sub_url': response.request.url if response else kwargs.get('sub_url'),
            'sub_data': response.request.body if response else kwargs.get('sub_data'),
            'sub_response': response.content if response else kwargs.get('sub_response'),
            'sub_request_time': response.elapsed if response else kwargs.get('sub_request_time'),

            # Type and Reference Number
            'sub_typ': kwargs.get('sub_typ'),
            'sub_refnr': kwargs.get('sub_refnr'),

            # Data from the bpk company
            'sub_company_mode': kwargs.get('sub_mode') or self.bpk_company_id.fa_dr_mode,
            'sub_company_type': kwargs.get('sub_company_type') or self.bpk_company_id.fa_dr_type,

            # Error information
            'error_text': kwargs.get('error_text'),

            # Skipped information
            'skipped_by_id': kwargs.get('skipped_by_id'),
            'skipped': kwargs.get('skipped'),

            # BPK data
            'sub_bpk_id': bpk.id if bpk else None,
            'sub_bpk_company_name': bpk.BPKRequestCompanyID.name if bpk else None,
            'sub_bpk_company_stammzahl': bpk.BPKRequestCompanyID.stammzahl if bpk else None,
            'sub_bpk_private': bpk.BPKPrivate if bpk else None,
            'sub_bpk_public': bpk.BPKPublic if bpk else None,
            'sub_bpk_firstname': bpk.BPKRequestFirstname if bpk else None,
            'sub_bpk_lastname': bpk.BPKRequestLastname if bpk else None,
            'sub_bpk_birthdate': bpk.BPKRequestBirthdate if bpk else None,
            'sub_bpk_zip': bpk.BPKRequestZIP if bpk else None,
        }

        # Append to submission log
        values['sub_log'] = self.sub_log or '' + '%s\n---\n%s\n' % (fields.datetime.now(), pp.pprint(values))

        # TODO: Skip all anchestors (older) donation reports that are in state new, approved or error

        return self.write(values)

    # Donation report submission (Spendenquittungen and das Finanzam uebermitteln)
    @api.multi
    def submit_donation_report_to_fa(self):
        # SUBMIT DONATION REPORT(S) (Spendenmeldung)
        for report in self:
            # Check donation report state
            assert report.state in ('approved', 'error'), _("Donation reports must be in state 'approved' or 'error' "
                                                            "for submission to FinanceOnline")

            # Check donation_deduction_optout and donation_deduction_disabled
            if report.partner_id.donation_deduction_disabled:
                report._donation_report_update(state="error",
                                               error_text=_("Donation Deduction is disabled for this partner!"))
                continue
            if report.partner_id.donation_deduction_optout_web:
                report._donation_report_update(state="error",
                                               error_text=_("Donation Deduction OptOut is set for this partner!"))
                continue

            # Check for newer donation reports
            # If there are already follow-up reports this one can be skipped in favour of the newer one(s)
            follow_ups = self.search([('id', '!=', self.id),
                                      ('partner_id', '=', self.partner_id),
                                      ('bpk_company_id', '=', self.bpk_company_id),
                                      ('meldungs_jahr', '=', self.meldungs_jahr),
                                      ('anlage_am_um', '>', self.anlage_am_um)])
            if follow_ups:
                report._donation_report_update(state="skipped",
                                               error_text=_("Skipped! Newer donation reports found!\n"
                                                            "ids: %s") % follow_ups.ids)
                continue

            # Check if a BPK record with a public BPK key exits for this res.partner
            bpk = False
            bpk_error = False
            try:
                bpk = self._find_bpk_record()
                if not bpk:
                    bpk_error = _("No BPK record found!")
                if bpk and not bpk.BPKPublic:
                    bpk_error = _("No public BPK-Key found in the BPK record!")
            except Exception as e:
                    bpk_error = _("BPK record error!\n%s") % str(e)
            if bpk_error:
                report._donation_report_update(state="error", error_text=bpk_error)
                continue

            # Find the correct sub_typ ("Uebermittlungs_Typ") and refnr ("Referenznummer")
            # E = Erstmeldung (if there are no other submissions for this person for this meldungs_jahr)
            # A = Aenderung (if there are already send reports for this person with the same meldungs_jahr)
            #     !!!Ohne vbPK!!! ABER RefNr = RefNr der Erstmeldung!
            # S = Stornierung ( if the "betrag" is 0 or negative and there is a send report of type E or A
            #                   for this meldungs_jahr)
            #     !!!Ohne vbPK UND ohne Betrag!!! ABER RefNr = RefNr der Erstmeldung!
            #
            # Referenze-Number-Format example: DADI/1234/2017/E
            #
            sub_typ = False
            sub_refnr = False
            # Search for a former submission of type E (=Erstmeldung)
            erstmeldung = self.search([('id', '!=', self.id),
                                       ('partner_id', '=', self.partner_id),
                                       ('bpk_company_id', '=', self.bpk_company_id),
                                       ('meldungs_jahr', '=', self.meldungs_jahr),
                                       ('sub_typ', '=', 'E'),
                                       ('state', '=', 'submitted'),
                                       ('anlage_am_um', '<', self.anlage_am_um)],
                                      limit=1, order='anlage_am_um DESC')
            if erstmeldung:
                sub_typ = "A"
                sub_refnr = erstmeldung.sub_refnr
            else:
                sub_typ = "E"
                sub_refnr = "DADI/" + report.id + "/" + report.meldungs_jahr + "/" + sub_typ
            # Check for cancellation (Stornierung)
            if self.betrag <= 0:
                if erstmeldung:
                    sub_typ = "S"
                    sub_refnr = erstmeldung.sub_refnr
                else:
                    report._donation_report_update(state="skipped",
                                                   error_text=_("Skipped! Cancellation without former submissions."))
                    continue

            # Login to FinanzOnline
            # HINT: Todo: The login method must check if the session_id is still valid and re-login if not !!!
            bpk_company = report.bpk_company_id
            login_error = False
            try:
                session_id = bpk_company.finanz_online_login()
                if not session_id:
                    login_error = _("Login to FinanzOnline failed!")
            except Exception as e:
                login_error = _("Login to FinanzOnline failed!\n") + str(e)
                pass
            if login_error:
                report._donation_report_update(state="error", error_text=login_error)
                continue

            # TODO: Send donation report to FinanzOnline (FileUpload)
            # HTTP SOAP REQUEST
            addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            soaprequest_templates = pj(addon_path, 'soaprequest_templates')
            assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                          % soaprequest_templates
            fo_donation_report_template = pj(soaprequest_templates, 'fo_donation_report_j2template.xml')
            assert os.path.exists(fo_donation_report_template), _("fo_donation_report_j2template.xml not found at %s") \
                                                                % fo_donation_report_template
            fo_donation_report_data = {
                # Webservice Session parameter
                'tid': bpk_company.fa_tid,
                'benid': bpk_company.fa_benid,
                'id': bpk_company.fa_login_sessionid,
                # Sonderausgaben FileUpload parameter
                'art': 'UEB_SA',
                'uebermittlung': bpk_company.fa_dr_mode,
                # Info_Daten
                'Fastnr_Fon_Tn': bpk_company.fa_herstellerid,    # Steuernummer des Dienstleisters
                'Fastnr_Org': bpk_company.vat,                   # Steuernummer der Organisation
                # MessageSpec
                'MessageRefId': 'DADI/'+report.id,
                'Timestamp': fields.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                'Uebermittlungsart': bpk_company.fa_dr_type,
                'Zeitraum': report.meldungs_jahr,
                # Sonderausgaben
                'sub_typ': sub_typ,
                'RefNr': sub_refnr,
                'Betrag': '0' if report.betrag <= 0 else str(self.betrag),
                'vbPK': bpk.BPKPublic,
            }

            # Submit donation report to FinanzOnline
            try:
                response = soap_request(url='https://finanzonline.bmf.gv.at/fon/ws/fileupload',
                                        template=fo_donation_report_template,
                                        http_header={
                                            'content-type': 'text/xml; charset=utf-8',
                                            'SOAPAction': 'upload'
                                        },
                                        fo_donation_report=fo_donation_report_data)
            except Exception as e:
                error_msg = "Donation report submission to FinanzOnline failed!\n%s" % str(e)
                logger.error(error_msg)
                report._donation_report_update(state="error", bpk=bpk, error_text=error_msg)
                continue

            # Check for errors / response status code
            if response.status_code != 200:
                error_msg = _("Donation report submission to FinanzOnline failed! HTTP error"
                              "%s %s") % (response.status_code, response.reason)
                logger.error(error_msg)
                report._donation_report_update(response=response, bpk=bpk,
                                               state="error", error_text=error_msg,)
                continue

            # Process answer (response.content) as xml
            try:
                # Process xml answer
                parser = etree.XMLParser(remove_blank_text=True)
                response_etree = etree.fromstring(response.content, parser=parser)
            except Exception as e:
                error_msg = _("Could not parse FinanzOnline response as XML!\n"
                              "%s\nResponse Content:\n%s") % (str(e), response.content)
                logger.error(error_msg)
                report._donation_report_update(response=response, bpk=bpk,
                                               state="exception", error_text=error_msg,)
                continue

            # TODO: Find data in response.content xml and update donation report


    #
    # TODO: Add scheduler action and scheduler xml-data-record
    #
