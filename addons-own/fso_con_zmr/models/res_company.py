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

    # FIELDS
    BPKRequestIDS = fields.One2many(comodel_name="res.partner.bpk", inverse_name="BPKRequestCompanyID",
                                    string="BPK Requests")

    # Donation Reports
    #donation_report_ids = fields.One2many(comodel_name="res.partner.donation_report",
    #                                      inverse_name="bpk_company_id",
    #                                      string="Donation Reports", readonly=True)

    # Donation Report Submissions
    #donation_report_submission_ids = fields.One2many(comodel_name="res.partner.donation_report.submission",
    #                                                 inverse_name="bpk_company_id",
    #                                                 string="Donation Report Submissions", readonly=True)

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
    BPKRequestURL = fields.Selection(selection=[('https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR',
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

    # Austrian Finanz Amt: Finanz Online Webservice Session-Login Data
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

    # Austrian Finanz Amt: Finanz Online Webservice Session and Login Information
    fa_login_sessionid = fields.Char(string="Finanz Online Login SessionID", readonly=True)
    fa_login_returncode = fields.Char(string="Finanz Online Login Returncode", readonly=True)
    fa_login_message = fields.Text(string="Finanz Online Login Message", readonly=True)

    # Austrian Finanz Amt: Finanz Online donation report (Spendenmeldung)
    # TODO: remove obsolete Field fa_dr_mode
    fa_dr_mode = fields.Selection(selection=[('T', 'T: Testumgebung'),
                                             ('P', 'P: Echtbetrieb')],
                                  string="Spendenmeldung Modus (Veraltet)")
    fa_dr_type = fields.Selection(string="Spendenmeldung Uebermittlungsart",
                                  selection=[('KK', 'KK Einrichtung Kunst und Kultur (gem. § 4a Abs 2 Z 5 EStG)'),
                                             ('SO', 'SO Karitative Einrichtungen (gem § 4a Abs 2 Z3 lit a bis c EStG)'),
                                             ('FW', 'FW Wissenschaftseinrichtungen (gem. 4a Abs 2Z 1 EStG)'),
                                             ('NT', 'NT Naturschutz und Tierheime (gem § 4a Abs 2 Z 3 lit d und e EStG)'),
                                             ('SN', 'SN Sammeleinrichtungen Naturschutz (gem § 4a Abs 2 Z 3 lit d und e EStG)'),
                                             ('SG', 'SG gemeinnützige Stiftungen (§ 4b EStG 1988, hinsichtlich Spenden)'),
                                             ('UN', 'UN Universitätetn, Kunsthochschulen, Akademie der bildenden Künste (inkl. Fakultäten, Instituteund besondere Einrichtungen, § 4a Abs 3 Z 1 EStG)'),
                                             ('MÖ', 'MÖ Museen von Körperschaften öffentlichen Rechts (§ 4a Abs 4 lit b EStG)'),
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
    @api.depends('pvpToken_crt_pem', 'pvpToken_prvkey_pem')
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
                # Write path to field
                rec.pvpToken_crt_pem_path = crt_pem_file
            if rec.pvpToken_prvkey_pem:
                prvkey_pem_file = pj(crt_dir, rec.pvpToken_prvkey_pem_filename)
                with open(prvkey_pem_file, 'w') as f:
                    f.write(rec.pvpToken_prvkey_pem.decode('base64'))
                # Write path to field
                rec.pvpToken_prvkey_pem_path = prvkey_pem_file

        # TODO: Delete old cert files on field changes (= new cert upload)

    # TODO: on deletion of a company delete all related res.partner.bpk records

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

        # Get the template-folder directory
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                      % soaprequest_templates
        # Get the logout-template path
        fo_logout_template = pj(soaprequest_templates, 'fo_logout_j2template.xml')
        assert os.path.exists(fo_logout_template), _("fo_logout_j2template.xml not found at %s") \
                                                   % fo_logout_template
        # Logout
        response = soap_request(url='https://finanzonline.bmf.gv.at:443/fonws/ws/sessionService',
                                template=fo_logout_template,
                                fo_logout={'tid': c.fa_tid,
                                           'benid': c.fa_benid,
                                           'id': c.fa_login_sessionid})
        # Process soap xml answer
        parser = etree.XMLParser(remove_blank_text=True)
        response_etree = etree.fromstring(response.content, parser=parser)
        returncode = response_etree.find(".//{*}rc")
        returncode = returncode.text if returncode is not None else False
        if returncode == "0":
            c.fa_login_sessionid = False
            c.fa_login_returncode = False
            c.fa_login_message = False
            logger.info(_("FinanzOnline logout was successful!"))
            return True
        else:
            response_pprint = etree.tostring(response_etree, pretty_print=True)
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

        # Check if there is already a session id (if we are already logged in)
        # TODO: !!! Check somehow is the sessionid is still valid !!!
        if c.fa_login_sessionid:
            return c.fa_login_sessionid

        # GET THE LOGIN TEMPLATE
        # Get the template-folder directory
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                      % soaprequest_templates
        # Get the login-template path
        fo_login_template = pj(soaprequest_templates, 'fo_login_j2template.xml')
        assert os.path.exists(fo_login_template), _("fo_login_j2template.xml not found at %s") \
                                                  % fo_login_template

        # CHECK FINANZ ONLINE LOGIN DATA
        mandatory_fields = ['fa_tid', 'fa_benid', 'fa_pin']
        missing = [field for field in mandatory_fields if not getattr(c, field)]
        if missing:
            c.fa_login_sessionid = False
            c.fa_login_returncode = False
            c.fa_login_message = False
        assert not missing, _("FinanzOnline webservice user information is missing! (%s)\n"
                              "Check company settings for %s (id: %s)") % (missing, c.name, c.id)

        # HTTP SOAP REQUEST
        response = soap_request(url='https://finanzonline.bmf.gv.at:443/fonws/ws/sessionService',
                                template=fo_login_template,
                                fo_login={'tid': c.fa_tid,
                                          'benid': c.fa_benid,
                                          'pin': c.fa_pin,
                                          'herstellerid': c.fa_herstellerid})
        # Process soap xml answer
        parser = etree.XMLParser(remove_blank_text=True)
        response_etree = etree.fromstring(response.content, parser=parser)
        response_pprint = etree.tostring(response_etree, pretty_print=True)

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
