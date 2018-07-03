# -*- coding: utf-8 -*-

from openerp import api, models, fields
from openerp.tools import config
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.soap import soap_request

from lxml import etree
import os
from os.path import join as pj
import errno
import logging
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class CompanyAustrianZMRSettings(models.Model):
    _inherit = 'res.company'

    # ------
    # FIELDS
    # ------
    bpk_request_ids = fields.One2many(string="BPK Requests", readonly=True,
                                      comodel_name="res.partner.bpk", inverse_name="bpk_request_company_id")

    # Donation Reports
    donation_report_ids = fields.One2many(string="Donation Reports", readonly=True,
                                          comodel_name="res.partner.donation_report", inverse_name="bpk_company_id")

    # Donation Report Submissions
    donation_report_submission_ids = fields.One2many(comodel_name="res.partner.donation_report.submission",
                                                     inverse_name="bpk_company_id",
                                                     string="Donation Report Submissions", readonly=True)

    # Basic Settings
    stammzahl = fields.Char(string="Firmenbuch-/ Vereinsregisternummer", help='Stammzahl e.g.: XZVR-123456789')

    # PVPToken userPrincipal
    pvpToken_userId = fields.Char(string="User ID (userId)")
    pvpToken_cn = fields.Char(string="Common Name (cn)")
    pvpToken_gvOuId = fields.Char(string="Request Organisation (gvOuId)")
    pvpToken_ou = fields.Char(string="Request Person (ou)")

    # ZMR Requests SSL Zertifikate
    # http://www.ridingbytes.com/2016/01/02/odoo-remember-the-filename-of-binary-files/
    pvpToken_crt_pem = fields.Binary(string="Certificate (PEM)")
    pvpToken_crt_pem_filename = fields.Char(string="Certificate Name", help="crt_pem")
    pvpToken_crt_pem_path = fields.Char(string="Certificate Path",
                                        compute='_certs_to_file', compute_sudo=True, store=True, readonly=True)

    pvpToken_prvkey_pem = fields.Binary(string="Private Key (PEM)")
    pvpToken_prvkey_pem_filename = fields.Char(string="Private Key Name", help="prvkey_pem without password!")
    pvpToken_prvkey_pem_path = fields.Char(string="Private Key Path",
                                           compute='_certs_to_file', compute_sudo=True, store=True, readonly=True)
    # Get BPK request URLS
    bpk_request_url = fields.Selection(selection=[('https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR',
                                                 'Test: https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR'),
                                                ('https://pvawp.bmi.gv.at/bmi.gv.at/soap/SZ2Services/services/SZR',
                                                 'Live: https://pvawp.bmi.gv.at/bmi.gv.at/soap/SZ2Services/services/SZR'),
                                                ],
                                     string="GetBPK Request URL",
                                     default="https://pvawp.bmi.gv.at/bmi.gv.at/soap/SZ2Services/services/SZR")
    # BPK-Request Status messages
    bpk_found = fields.Text(string="BPK Person-Found Message", translate=True)
    bpk_not_found = fields.Text(string="BPK No-Person-Matched Message", translate=True)
    bpk_multiple_found = fields.Text(string="BPK Multiple-Person-Matched Message", translate=True)
    bpk_zmr_service_error = fields.Text(string="BPK ZMR-Service-Error Message", translate=True)

    # Austrian Finanzamt: FinanzOnline Webservice Session-Login Data
    # https://www.bmf.gv.at/egovernment/fon/fuer-softwarehersteller/softwarehersteller-funktionen.html#Webservices
    fa_tid = fields.Char(string="Teilnehmer Identifikation (tid)")
    fa_benid = fields.Char(string="Webservicebenutzer ID (benid)")
    fa_pin = fields.Char(string="Webservicebenutzer Pin (pin)")
    fa_herstellerid = fields.Char(string="UID-Nummer des Softwareherstellers (herstellerid)",
                                  help="Umsatzsteuer-Identifikations-Nummer (UID-Nummer) des Softwareherstellers.",
                                  default="ATU44865400", size=24)

    # Austrian Finanz Amt: Finanz Online donation report submission (Spendenmeldung Meldung):
    # Fastnr_Fon_Tn
    fa_fastnr_fon_tn = fields.Char(string="Finanzamt-Steuernummer des Softwareherstellers (Fastnr_Fon_Tn)",
                                   help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus dem "
                                        "Finanzamt (03-98) und aus der Steuernummer (7-stellig) zusammen. "
                                        "(ohne Trennzeichen) (Fastnr_Fon_Tn)",
                                   default="685032617", size=9)
    # Fastnr_Org
    fa_fastnr_org = fields.Char(string="Finanzamt-Steuernummer der Organisation (Fastnr_Org)",
                                help="Die Finanzamt/Steuernummer besteht aus 9 Ziffern und setzt sich aus dem "
                                     "Finanzamt (03-98) und aus der Steuernummer (7-stellig) zusammen. "
                                     "(ohne Trennzeichen) (Fastnr_Org)",
                                size=9, oldname="fa_orgid")

    # FinanzOnline Requests SSL Zertifikate
    # http://www.ridingbytes.com/2016/01/02/odoo-remember-the-filename-of-binary-files/
    fa_crt_pem = fields.Binary(string="Certificate (PEM)")
    fa_crt_pem_filename = fields.Char(string="Certificate Name", help="crt_pem")
    fa_crt_pem_path = fields.Char(string="Certificate Path",
                                  compute='_certs_to_file', compute_sudo=True, store=True, readonly=True)

    fa_prvkey_pem = fields.Binary(string="Private Key (PEM)")
    fa_prvkey_pem_filename = fields.Char(string="Private Key Name", help="prvkey_pem without password!")
    fa_prvkey_pem_path = fields.Char(string="Private Key Path",
                                     compute='_certs_to_file', compute_sudo=True, store=True, readonly=True)

    # Austrian Finanz Amt: Finanz Online Webservice Session and Login Information
    fa_login_sessionid = fields.Char(string="FinanzOnline Login SessionID", readonly=True)

    fa_login_returncode = fields.Char(string="FinanzOnline Login Returncode", readonly=True)
    fa_login_message = fields.Text(string="FinanzOnline Login Message", readonly=True)
    fa_login_time = fields.Datetime(string="FinanzOnline Last Login Request", readonly=True)

    fa_logout_returncode = fields.Char(string="FinanzOnline Logout Returncode", readonly=True)
    fa_logout_message = fields.Text(string="FinanzOnline Logout Message", readonly=True)
    fa_logout_time = fields.Datetime(string="FinanzOnline Last Logout Request", readonly=True)

    # Austrian Finanz Amt: Finanz Online donation report (Spendenmeldung)
    # ATTENTION: fa_dr_mode is DEPRICATED and not used anymore - should already be removed everywhere!
    fa_dr_mode = fields.Selection(selection=[('T', 'T: Testumgebung'),
                                             ('P', 'P: Echtbetrieb')],
                                  string="Spendenmeldung Modus (Veraltet)", readonly=True)

    # ATTENTION: MO MUST BE MÖ but Ö is not allowed in selection fields :( - This is replaced in the
    #            donation_report.submission field submission_fa_dr_type! Check compute_submission_values() for the fix.
    #            It is an ugly fix but right now there seems to be no other quick way
    fa_dr_type = fields.Selection(string="Spendenmeldung Uebermittlungsart",
                                  help=_("This Field is mandatory for donation report submissions!"),
                                  selection=[('KK', 'KK Einrichtung Kunst und Kultur (gem. § 4a Abs 2 Z 5 EStG)'),
                                             ('SO', 'SO Karitative Einrichtungen (gem § 4a Abs 2 Z3 lit a bis c EStG)'),
                                             ('FW', 'FW Wissenschaftseinrichtungen (gem. 4a Abs 2Z 1 EStG)'),
                                             ('NT', 'NT Naturschutz und Tierheime (gem § 4a Abs 2 Z 3 lit d und e EStG)'),
                                             ('SN', 'SN Sammeleinrichtungen Naturschutz (gem § 4a Abs 2 Z 3 lit d und e EStG)'),
                                             ('SG', 'SG gemeinnützige Stiftungen (§ 4b EStG 1988, hinsichtlich Spenden)'),
                                             ('UN', 'UN Universitätetn, Kunsthochschulen, Akademie der bildenden Künste (inkl. Fakultäten, Instituteund besondere Einrichtungen, § 4a Abs 3 Z 1 EStG)'),
                                             ('MO', 'MÖ Museen von Körperschaften öffentlichen Rechts (§ 4a Abs 4 lit b EStG)'),    # ATTENTION MO is replaced by MÖ for the donation report
                                             ('MP', 'MP Privatmuseen mit überregionaler Bedeutung (§ 4a Abs 4 lit b EStG)'),
                                             ('FF', 'FF Freiwillige Feuerwehren ( § 4a Abs 6 EStG) und Landesfeuerwehrverbände (§ 4a Abs 6 EStG)'),
                                             ('KR', 'KR Kirchen und Religionsgesellschaften mit verpflichtenden Beiträgen (§ 18 Abs 1 Z 5 EStG)'),
                                             ('PA', 'PA Pensionsversicherungsanstalten und Versorgungseinrichtungen (§ 18 Abs 1 Z 1a EStG)'),
                                             ('SE', 'SE Behindertensportdachverbände, Internationale Anti-Korruptions-Akademie, Diplomatische Akademie (§ 4a Abs 4 EStG)'),
                                             ('ZG', 'ZG gemeinnützige Stiftungen (§ 4b EStG, hinsichtlich Zuwendungen zur Vermögensausstattung)')],
                                  )

    # Action to store certificate files to data dir because request.Session(cert=()) needs file paths
    # https://www.odoo.com/de_DE/forum/hilfe-1/question/
    #     is-there-a-way-to-get-the-location-to-your-odoo-and-to-create-new-files-in-your-custom-module-89677
    @api.depends('pvpToken_crt_pem', 'pvpToken_prvkey_pem', 'fa_crt_pem', 'fa_prvkey_pem')
    def _certs_to_file(self):
        # http://stackoverflow.com/questions/21458155/get-file-path-from-binary-data
        assert config['data_dir'], "config['data_dir'] missing!"
        assert self.env.cr.dbname, "self.env.cr.dbname missing!"
        assert self.env.user.company_id.id, "self.env.user.company_id.id missing!"
        crt_dir = pj(config['data_dir'], "filestore", self.env.cr.dbname,
                     "fso_con_zmr", "company_"+str(self.env.user.company_id.id))
        if not os.path.exists(crt_dir):
            try:
                os.makedirs(crt_dir)
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise
        for rec in self:
            
            if rec.pvpToken_crt_pem:
                crt_pem_file = pj(crt_dir, rec.pvpToken_crt_pem_filename)
                with open(crt_pem_file, 'w') as f:
                    f.write(rec.pvpToken_crt_pem.decode('base64'))
                rec.pvpToken_crt_pem_path = crt_pem_file
            
            if rec.pvpToken_prvkey_pem:
                prvkey_pem_file = pj(crt_dir, rec.pvpToken_prvkey_pem_filename)
                with open(prvkey_pem_file, 'w') as f:
                    f.write(rec.pvpToken_prvkey_pem.decode('base64'))
                rec.pvpToken_prvkey_pem_path = prvkey_pem_file

            if rec.fa_crt_pem:
                fa_crt_pem_file = pj(crt_dir, rec.fa_crt_pem_filename)
                with open(fa_crt_pem_file, 'w') as f:
                    f.write(rec.fa_crt_pem.decode('base64'))
                rec.fa_crt_pem_path = fa_crt_pem_file

            if rec.fa_prvkey_pem:
                fa_prvkey_pem_file = pj(crt_dir, rec.fa_prvkey_pem_filename)
                with open(fa_prvkey_pem_file, 'w') as f:
                    f.write(rec.fa_prvkey_pem.decode('base64'))
                rec.fa_prvkey_pem_path = fa_prvkey_pem_file

        # TODO: Delete old cert files on field changes (= new cert upload)

    # TODO: on deletion of a company delete all related res.partner.bpk records! For this we must change the old trigger
    #       names or any cascade delete will not work

    @api.multi
    def finanz_online_logout(self):
        assert self.ensure_one(), _("finanz_online_logout() can only be used for one company at a time!")
        c = self
        if not c.fa_login_sessionid:
            return True

        # Check Webservice User Data for Logout
        mandatory_fields = ['fa_tid', 'fa_benid', 'fa_login_sessionid']
        missing = [field for field in mandatory_fields if not getattr(c, field)]
        assert not missing, _("FinanzOnline webservice user information is missing! (%s)\n"
                              "Check company settings for %s (id: %s)") % (missing, c.name, c.id)

        returncode = ''
        try:
            # Get the template-folder directory
            addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            soaprequest_templates = pj(addon_path, 'soaprequest_templates')
            assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at "
                                                            "%s") % soaprequest_templates
            # Get the logout-template path
            fo_logout_template = pj(soaprequest_templates, 'fo_logout_j2template.xml')
            assert os.path.exists(fo_logout_template), _("fo_logout_j2template.xml not found at "
                                                         "%s") % fo_logout_template
            # Logout
            response = soap_request(url='https://finanzonline.bmf.gv.at:443/fonws/ws/sessionService',
                                    crt_pem=c.fa_crt_pem_path,
                                    prvkey_pem=c.fa_prvkey_pem_path,
                                    template=fo_logout_template,
                                    fo_logout={'tid': c.fa_tid,
                                               'benid': c.fa_benid,
                                               'id': c.fa_login_sessionid})
            # Process soap xml answer
            parser = etree.XMLParser(remove_blank_text=True)
            response_etree = etree.fromstring(response.content, parser=parser)
            response_pprint = etree.tostring(response_etree, pretty_print=True)

            # Store the answer and the logout request time
            c.fa_logout_message = response_pprint
            c.fa_logout_time = fields.datetime.now()

            # Find and store the return code
            returncode = response_etree.find(".//{*}rc")
            returncode = returncode.text if returncode is not None else False
            c.fa_logout_returncode = returncode
        except Exception as e:
            logger.error("FinanzOnline Logout Exception:\n%s" % repr(e))
            c.fa_logout_message = repr(e)
            c.fa_logout_time = fields.datetime.now()
            c.fa_logout_returncode = False
            pass

        # Clear login data
        c.fa_login_sessionid = False
        c.fa_login_returncode = False
        c.fa_login_message = False

        # Return True or False
        # HINT: -1 = Die Session ID ist ungueltig oder abgelaufen.
        if returncode in ["0", "-1"]:
            logger.info(_("FinanzOnline logout was successful!"))
            return True
        else:
            logger.error(_("FinanzOnline logout error!\n%s") % response_pprint)
            return False

    # --------------
    # RECORD ACTIONS
    # --------------
    @api.multi
    def finanz_online_login(self):
        """
        Will login to Finanz Online and store the acquired session id in the company field "fa_login_sessionid"

        :return: session_id or False
        """
        # Allow only for recordsets with one record to make the return easier
        assert self.ensure_one(), _("finanz_online_login() can only be used for one company at a time!")
        c = self

        # Logout first
        # ------------
        # HINT: sessionids are only valid for a couple of minutes in FinanzOnline so its no problem to always try
        #       to logout because nearly every request to FinanzOnline needs a new session id because the old one is
        #       expired. -> If possible we should check here if the session id is still valid or not but right now
        #       i don't know how?
        c.finanz_online_logout()

        # CHECK FINANZ ONLINE LOGIN DATA
        mandatory_fields = ['fa_tid', 'fa_benid', 'fa_pin']
        missing = [field for field in mandatory_fields if not getattr(c, field)]
        if missing:
            c.fa_login_sessionid = False
            c.fa_login_returncode = False
            c.fa_login_message = False
            c.fa_login_time = False
        assert not missing, _("FinanzOnline webservice user information is missing! (%s)\n"
                              "Check company settings for %s (id: %s)") % (missing, c.name, c.id)

        # GET THE LOGIN TEMPLATE
        # Get the template-folder directory
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s"
                                                        "") % soaprequest_templates
        # Get the login-template path
        fo_login_template = pj(soaprequest_templates, 'fo_login_j2template.xml')
        assert os.path.exists(fo_login_template), _("fo_login_j2template.xml not found at %s"
                                                    "") % fo_login_template

        # HTTP SOAP REQUEST
        response = soap_request(url='https://finanzonline.bmf.gv.at:443/fonws/ws/sessionService',
                                crt_pem=c.fa_crt_pem_path,
                                prvkey_pem=c.fa_prvkey_pem_path,
                                template=fo_login_template,
                                fo_login={'tid': c.fa_tid,
                                          'benid': c.fa_benid,
                                          'pin': c.fa_pin,
                                          'herstellerid': c.fa_herstellerid})
        # Process soap xml answer
        parser = etree.XMLParser(remove_blank_text=True)
        response_etree = etree.fromstring(response.content, parser=parser)
        response_pprint = etree.tostring(response_etree, pretty_print=True)

        # Store login request time
        c.fa_login_time = fields.datetime.now()

        # Check for http errors
        if response.status_code != 200:
            c.fa_login_sessionid = False
            c.fa_login_returncode = False
            c.fa_login_message = response_pprint
            logger.error(_("FinanzOnline login error!\n%s") % response_pprint)
            return False

        # Check the return code
        # https://www.bmf.gv.at/egovernment/fon/fuer-softwarehersteller/softwarehersteller-funktionen.html#Webservices
        # 0 = Aufruf ok
        # -1 = Die Session ID ist ungueltig oder abgelaufen.
        # -2 = Der Aufruf des Webservices ist derzeit wegen Wartungsarbeiten nicht moeglich.
        # -3 = Es ist ein technischer Fehler aufgetreten.
        # -4 = Die uebermittelten Zugangsdaten sind ungueltig.
        # -5 = Benutzer nach mehreren Fehlversuchen gesperrt.
        # -6 = Der Benutzer ist gesperrt.
        # -7 = Der Benutzer ist kein Webservice-User.
        returncode = response_etree.find(".//{*}rc")
        returncode = returncode.text if returncode is not None else False

        # Login was successful
        if returncode == '0':
            session_id = response_etree.find(".//{*}id").text
            if not session_id:
                c.fa_login_returncode = False
                c.fa_login_message = response_pprint
                logger.error(_("FinanzOnline login error! Could not find Session ID in:\n%s") % response_pprint)
                assert session_id, _("finanz_online_login() "
                                     "Returncode is ok but session id was not found in \n%s") % response_pprint
            c.fa_login_sessionid = session_id
            c.fa_login_returncode = returncode
            c.fa_login_message = "Login OK"
            logger.info(_("FinanzOnline login was successful!"))
            return session_id
        # Login error
        else:
            logger.error(_("FinanzOnline login error! Bad returncode:\n%s") % response_pprint)
            c.fa_login_sessionid = False
            c.fa_login_returncode = returncode
            msg = response_etree.find(".//{*}msg")
            c.fa_login_message = msg.text if msg is not None else response_pprint
            return False

    @api.multi
    def set_donation_reports_to_error_state(self):
        for c in self:
            donation_reports = self.env['res.partner.donation_report']

            # Make sure all donation reports that could be submitted will be set to 'error' so they can only be
            # submitted after a state recomputation.
            donation_reports = donation_reports.sudo().search([('bpk_company_id', '=', c.id),
                                                               '|',
                                                                   ('state', '=', False),
                                                                   ('state', '=', 'new')])
            if donation_reports:
                logger.info("Set the state from new to error for %s donation reports because company data changed!"
                            "" % len(donation_reports))
                donation_reports.write({
                    'state': 'error',
                    'submission_id': False,
                    'submission_type': False,
                    'submission_refnr': False,
                    'report_erstmeldung_id': False,
                    'skipped_by_id': False,
                    'cancelled_lsr_id': False,
                    #
                    'submission_firstname': False,
                    'submission_lastname': False,
                    'submission_birthdate_web': False,
                    'submission_zip': False,
                    #
                    'submission_bpk_request_id': False,
                    'submission_bpk_public': False,
                    'submission_bpk_private': False,
                    #
                    'error_type': 'company_data_changed',
                    'error_code': False,
                    'error_detail': 'State recomputation is necessary because the company data changed! '
                                    'Use the prepared scheduled action for this under planed actions.',
                })
                logger.info("Set the state to error for %s donation reports DONE!" % len(donation_reports))

        logger.info("Recompute state for donation reports by a cron job in the background!")
        donation_reports.cron_compute_donation_report_state()

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values):

        # Create the company in the current environment (memory only right now i guess)
        # ATTENTION: self is still empty but the company exits in the 'res' recordset already
        res = super(CompanyAustrianZMRSettings, self).create(values)

        if res:
            # Update donation reports
            res.update_donation_reports()

        return res

    @api.multi
    def write(self, values):

        # ATTENTION: !!! After this 'self' is changed (in memory i guess)
        #                'res' is only a boolean !!!
        res = super(CompanyAustrianZMRSettings, self).write(values)

        # Update donation reports on any change to FinanzOnline related fields
        if res:
            fields_to_check = ['fa_herstellerid', 'fa_fastnr_fon_tn', 'fa_fastnr_org', 'fa_dr_type']
            if any(f in values for f in fields_to_check):
                logger.info("Company data relevant for donation reports changed!")
                self.set_donation_reports_to_error_state()

        return res
