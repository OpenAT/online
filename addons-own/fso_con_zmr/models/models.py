# -*- coding: utf-8 -*-
import os
import errno
from os.path import join as pj
import openerp
from openerp import api, models, fields
from openerp.exceptions import ValidationError, Warning
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.soap import soap_request
from lxml import etree
import time
from datetime import timedelta
import logging
import datetime
from openerp.tools import config
import re
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


def clean_name(name, split=False):
    # https://github.com/OpenAT/online/issues/64
    # HINT: Char fields are always unicode in odoo which is good therefore do not convert any Char fields with str()!
    # ATTENTION: Flags like re.UNICODE do NOT work all the time! Use (?u) instead in the start of any regex pattern!

    # Replace u., und, & with +
    name = re.sub(ur"(?u)[&]+", "+", name)
    name = re.sub(ur"(?iu)\b(und|u)\b", "+", name)
    # Remove right part starting with first +
    name = name.split('+')[0]
    # Remove unwanted words case insensitive (?i)
    # HINT: This may leave spaces or dots after the words but these get cleaned later on anyway
    name = re.sub(ur"(?iu)\b(fam|familie|sen|jun|persönlich|privat|c[/]o|anonym|e[.]u)\b", "", name)
    # Remove Numbers
    name = ''.join(re.findall(ur"(?u)[^0-9]+", name))
    # Keep only unicode alphanumeric-characters (keeps chars like e.g.: Öö ỳ Ṧ), dash and space
    # HINT: This removes the left over dots from e.g.: Sen. or e.u
    name = ''.join(re.findall(ur"(?u)[\w\- ]+", name))
    # Remove leading and trailing: whitespace and non alphanumeric characters
    name = re.sub(ur"(?u)^[\W]*|[\W]*$", "", name)
    # Replace multiple dashes with one dash
    name = re.sub(ur"(?u)-[\s\-]*-+", "-", name)
    # Remove whitespace around dashes
    name = re.sub(ur"(?u)\s*-\s*", "-", name)
    # Replace multiple spaces with one space
    name = re.sub(ur"(?u)\s\s+", " ", name)
    # Use only first word of name
    if split:
        # Search from start until first non unicode alphanumeric-character which is not a - is reached
        # HINT: Can only be space or dash at this point ;)
        name = ''.join(re.findall(ur"(?u)^[\w\-]+", name))

    return name


class CompanyAustrianZMRSettings(models.Model):
    _inherit = 'res.company'

    # FIELDS
    BPKRequestIDS = fields.One2many(comodel_name="res.partner.bpk", inverse_name="BPKRequestCompanyID",
                                    string="BPK Requests")

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

    # TODO: on deletion of a company delete all related res.partner.bpk records


class ResPartnerBPK(models.Model):
    _name = 'res.partner.bpk'

    # FIELDS
    # res.company
    BPKRequestCompanyID = fields.Many2one(comodel_name='res.company', string="BPK Request Company",
                                          required=True, readonly=True)

    # res.partner
    BPKRequestPartnerID = fields.Many2one(comodel_name='res.partner', string="BPK Request Partner",
                                          required=True, readonly=True)

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


class ResPartnerZMRGetBPK(models.Model):
    _inherit = 'res.partner'

    # FIELDS
    BPKRequestIDS = fields.One2many(comodel_name="res.partner.bpk", inverse_name="BPKRequestPartnerID",
                                    string="BPK Requests")
    # BPK forced request values
    # TODO: Make sure Forced BPK Fields are always all filled or none (now only done by attr in the form view)
    BPKForcedFirstname = fields.Char(string="BPK Forced Firstname")
    BPKForcedLastname = fields.Char(string="BPK Forced Lastname")
    BPKForcedBirthdate = fields.Date(string="BPK Forced Birthdate")
    BPKForcedZip = fields.Date(string="BPK Forced ZIP")

    # Will be set when the BPK request processing of one batch of partners from the queue starts and
    # cleared again after the processing of the batch has finished
    BPKRequestInProgress = fields.Datetime(string="BPK Request in progress", readonly=True)

    # A Cron jobs that starts every minute will process all partners with BPKRequestNeeded set.
    # HINT: Normally set at res.partner write() (or create()) if any BPK relevant data was set or has changed
    # HINT: Changed from readonly to writeable to allow users to manually force BPK requests
    BPKRequestNeeded = fields.Datetime(string="BPK Request needed", readonly=False)

    # Store the last BPK Request date also at the partner to make searching for BPKRequestNeeded easier
    LastBPKRequest = fields.Datetime(string="Last BPK Request", readonly=True)

    # In case the BPK request throws an Exception instead of returning a result we store the exception text here
    BPKRequestError = fields.Text(string="BPK Request Exception!")

    # TODO optional: computed state field
    # HINT: colors="red:BPKRequestDate == False and BPKErrorRequestDate;
    #               orange:BPKRequestDate &lt; BPKErrorRequestDate;
    #               green:BPKRequestDate &gt; BPKErrorRequestDate"
    # HINT: This field shows only the state of the current bpk requests and does not check if current data is still
    # ATTENTION: Date fields are in char format - make sure greater than or lower than comparison works as expected
    # BPKRequestState = fields.Selection(
    #     selection=[('data_incomplete', 'Data incomplete'),         # BPKRequestNeeded=False and no BPK Requests linked
    #                ('pending', 'BPK Request Scheduled'),           # BPKRequestNeeded is set
    #                ('bpk_ok', 'BPK OK'),                           # any(BPKRequestDate > BPKErrorRequestDate)
    #                ('bpk_ok_old', 'BPK OK with old Data'),         # any(BPKRequestDate < BPKErrorRequestDate)
    #                ('bpk_error', 'Error')],                        # any(Not BPKRequestDate and BPKErrorRequestDate)
    #     string="BPK Request(s) State", compute=_compute_bpk_request_state, store=True)

    # Method to store BPK Fields
    def _bpk_regular_fields(self):
        return ['firstname', 'lastname', 'birthdate_web', 'zip']

    def _bpk_forced_fields(self):
        return ['BPKForcedFirstname', 'BPKForcedLastname', 'BPKForcedBirthdate', 'BPKForcedZip']

    def _bpk_fields(self):
        return self._bpk_regular_fields() + self._bpk_forced_fields()

    # Compute BPKRequestNeeded
    @api.multi
    def write(self, vals):
        """Override write to check for BPKRequestNeeded"""

        # No Checks if Donation Deduction Opt Out is going to be set to True
        # HINT: Manually set BPKRequestNeeded does not matter if donation_deduction_optout_web is set to True
        if vals.get('donation_deduction_optout_web', False):
            vals['BPKRequestNeeded'] = None
            return super(ResPartnerZMRGetBPK, self).write(vals)

        # No Checks if BPKRequestNeeded is set manually
        # HINT: This is useful for manually adding partners to the queue or to suppress immediate BPK checks
        # ATTENTION: sosync v1 and v2 will NOT sync the field BPKRequestNeeded but they may send it to suppress
        #            immediate bpk request checks after partner creation or update.
        #            This is only used after BPK file imports in FS.
        if 'BPKRequestNeeded' in vals:
            return super(ResPartnerZMRGetBPK, self).write(vals)

        # Compute BPKRequestNeeded
        # ------------------------
        # HINT: Even if there is already a BPK-Request we can assume that if data changed the bpkrequest needs to be
        #       done again. This may not be 100% exact but is fast and easy and false positives are no problem anyway!

        # Check if there is any BPK relevant field in vals
        fields_to_check = [field for field in self._bpk_fields() if field in vals]
        partners_bpk_needed = []

        if fields_to_check:
            # ATTENTION: Since sosync v1 always sends all fields, even if they are empty or unchanged,
            #            we need to really compare the values of the fields.
            partners_bpk_needed = self.env['res.partner']
            for p in self:

                # 1.) Skip any further testing if donation_deduction_optout_web is set for this partner
                if p.donation_deduction_optout_web:
                    if p.BPKRequestNeeded:
                        p.BPKRequestNeeded = None
                    continue

                # 2.) Check for forced BPK field changes
                if any(p[forced_field] for forced_field in self._bpk_forced_fields(self)):
                    # Check for any updates
                    forced_fields_to_check = [field for field in self._bpk_forced_fields() if field in vals]
                    if any(p[field] != vals[field] for field in forced_fields_to_check):
                        partners_bpk_needed = partners_bpk_needed | p
                    continue

                # 3.) Check for regular BPK field changes
                # HINT: Only check regular fields if forced fields are NOT set for this partner
                if not any(p[forced_field] for forced_field in self._bpk_forced_fields()):
                    regular_fields_to_check = [field for field in self._bpk_regular_fields() if field in vals]
                    if any(p[field] != vals[field] for field in regular_fields_to_check):
                        partners_bpk_needed = partners_bpk_needed | p
                    continue

        # Update BPKRequestNeeded
        # -----------------------
        if partners_bpk_needed:
            # If all partners needs to be updated we can add BPKRequestNeeded to vals
            if partners_bpk_needed == self:
                vals['BPKRequestNeeded'] = fields.datetime.now()
            # If only some partners needs to be updated we write them one by one before writing vals to them all
            else:
                for p in partners_bpk_needed:
                    p.BPKRequestNeeded = fields.datetime.now()

        return super(ResPartnerZMRGetBPK, self).write(vals)

    # INTERNAL METHODS
    def _find_bpk_companies(self):
        """
        :return: res.company recordset
        """
        # Find all companies with fully filled pvpToken Header fields
        # ATTENTION: Char Fields (and ONLY Char fields) in odoo domains should be checked with 'not in', [False, '']
        #            Because the sosyncer v1 wrote empty strings "" to Char fields instead of False :(
        #            This may be replaced by just xyz '!=', False after db cleanup and sosyncer v2
        companies = self.env['res.company'].sudo().search([('stammzahl', 'not in', [False, '']),
                                                           ('pvpToken_userId', 'not in', [False, '']),
                                                           ('pvpToken_cn', 'not in', [False, '']),
                                                           ('pvpToken_crt_pem', '!=', False),
                                                           ('pvpToken_prvkey_pem', '!=', False),
                                                           ('BPKRequestURL', '!=', False)])

        # Assert that all companies have the same BPKRequestURL Setting (Either test or live)
        if len(companies) > 1:
            request_url = companies[0].BPKRequestURL
            assert all((c.BPKRequestURL == request_url for c in companies)), _("All companies must use the same "
                                                                               "BPKRequestURL!")
        return companies

    def _request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str()):
        """
        Send BPK Request to the Austrian ZMR for every company with complete ZMR access data
        :param firstname:
        :param lastname:
        :param birthdate:
        :param zipcode:
        :return: list(), Containing one result-dict for every company found
                         (at least one result is always in the list ELSE it would throw an exception)
        """
        responses = list()

        # Validate input
        if not all((firstname, lastname, birthdate)):
            raise ValidationError(_("Missing input data! Mandatory are firstname, lastname and birthdate!"))

        # Get the request_data_template path
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                      % soaprequest_templates
        getbpk_template = pj(soaprequest_templates, 'GetBPK_small_j2template.xml')
        assert os.path.exists(soaprequest_templates), _("GetBPK_small_j2template.xml not found at %s") \
                                                      % getbpk_template

        # Find all companies with fully filled ZMR access fields
        companies = self._find_bpk_companies()
        assert companies, _("No company found with complete Austrian-ZMR BPK-Request access data!")

        for c in companies:
            # Check if the certificate files still exists at given path and restore them if not
            if not os.path.exists(c.pvpToken_crt_pem_path) or not os.path.exists(c.pvpToken_prvkey_pem_path):
                logger.warning(_("_request_bpk: Certificate data found but files on drive missing. "
                                 "Trying to restore files!"))
                c._certs_to_file()

            # Result interface
            result = {'company_id': c.id,
                      'company_name': c.name,
                      'request_date': datetime.datetime.now(),
                      'request_data': "",
                      'request_url': c.BPKRequestURL,
                      'response_http_error_code': "",
                      'response_content': "",
                      'response_time_sec': "",
                      'private_bpk': "",
                      'public_bpk': "",
                      'faultcode': "",
                      'faulttext': "",
                      }
            try:
                # HINT: In der Anwenderbeschreibung steht das man fuer private und oeffentliche BPK Anfragen eine
                #       unterschiedliche Bereichskennung und target Bereichskennung verwenden muss. Dies wird jedoch
                #       in der selben Beschreibung im Beispiel nicht verwendet sondern immer urn:publicid:gv.at:cdid+SA
                #       und urn:publicid:gv.at:wbpk+XZVR+123456789 um beide BPKs zu bekommen?!?
                #       Gefunden in: szr-3.0-anwenderdokumentation_v3_4.pdf
                # Private  BPK (unverschluesselt: Kann zur Dublettenerkennung verwendet werden)
                #              target_bereichskennung_privatebpk = "urn:publicid:gv.at:cdid+SA"
                #              bereichskennung_privatebpk = "urn:publicid:gv.at:cdid+" + cmp.stammzahl.replace('-', '+')
                # Public BPK (verschluesselt: Fuer die Uebermittlung der Spendensumme an das Bundesministerium fuer Finanzen)
                #            target_bereichskennung_publicbpk = "urn:publicid:gv.at:ecdid+BMF+SA"
                #            bereichskennung_publicbpk = "urn:publicid:gv.at:ecdid+" + cmp.stammzahl.replace('-', '+')
                # Daher wird hier die Bereichskennung und Target Bereichskennung so wie im Beispiel angegeben verwendet und
                # nicht wie weiter vorher im Text beschrieben.
                #
                #       BMF = Bundesministerium fuer Finanzen
                #       SA = Steuern und Abgaben

                start_time = time.time()
                response = soap_request(url=c.BPKRequestURL,
                                        template=getbpk_template,
                                        crt_pem=c.pvpToken_crt_pem_path, prvkey_pem=c.pvpToken_prvkey_pem_path,
                                        pvpToken={
                                            "authorize": {
                                                "role": ""
                                            },
                                            "authenticate": {
                                                "userPrincipal": {
                                                    "cn": c.pvpToken_cn,
                                                    "gvGid": "AT:VKZ:" + c.stammzahl,
                                                    "userId": c.pvpToken_userId,
                                                    "gvOuId": c.pvpToken_gvOuId,
                                                    "gvSecClass": "2",
                                                    "ou": c.pvpToken_ou
                                                },
                                                "participantId": "AT:VKZ:" + c.stammzahl
                                            }
                                        },
                                        GetBPK={
                                            "VKZ": c.stammzahl,
                                            "Target": {
                                                "BereichsKennung": "urn:publicid:gv.at:cdid+SA",
                                                "VKZ": "BMF"
                                            },
                                            "PersonInfo": {
                                                "Person": {
                                                    "Name": {
                                                        "GivenName": firstname,
                                                        "FamilyName": lastname
                                                    },
                                                    "DateOfBirth": birthdate,
                                                },
                                                "RegularDomicile": {
                                                    "PostalCode": zipcode,
                                                },
                                            },
                                            "BereichsKennung": "urn:publicid:gv.at:wbpk+" + c.stammzahl.replace('-',
                                                                                                                '+')
                                        },
                                        )
                assert response.content, _("GetBPK-Request response has no content!")
                result['request_data'] = response.request.body
                result['request_url'] = response.request.url
                response_time = time.time() - start_time
                result['response_time_sec'] = "%.3f" % response_time

                # Process soap xml answer
                parser = etree.XMLParser(remove_blank_text=True)
                response_etree = etree.fromstring(response.content, parser=parser)
                response_pprint = etree.tostring(response_etree, pretty_print=True)
                result['response_content'] = response_pprint

                # Response contains an error or is incomplete
                if response.status_code != 200:
                    result['response_http_error_code'] = response.status_code
                    error_code = response_etree.find(".//faultcode")
                    result['faultcode'] = error_code.text if error_code is not None else ""
                    error_text = response_etree.find(".//faultstring")
                    result['faulttext'] = error_text.text if error_text is not None else "ERROR"
                    # Update answer and process GetBPK for next company
                    responses.append(result)
                    continue

                # Response is valid
                # HINT: There is a namespace attached which needs to be ignored added or removed before .find()
                # http://stackoverflow.com/questions/4440451/how-to-ignore-namespaces-with-xpath
                private_bpk = response_etree.xpath(".//*[local-name() = 'GetBPKReturn']")
                assert len(private_bpk) == 1, _("More than one GetBPKReturn xml node found!")
                private_bpk = private_bpk[0]
                result['private_bpk'] = private_bpk.text if private_bpk is not None else result['private_bpk']
                public_bpk = response_etree.xpath(".//*[local-name() = 'FremdBPK']/*[local-name() = 'FremdBPK']")
                assert len(public_bpk) == 1, _("More than one FremdBPK xml node found!")
                public_bpk = public_bpk[0]
                result['public_bpk'] = public_bpk.text if public_bpk is not None else result['public_bpk']
                # Update answer and process GetBPK for next company
                responses.append(result)

            except Exception as e:
                result['faulttext'] = _("BPK Request Assertion:\n\n%s\n") % e
                responses.append(result)

        # Assert that all responses for the found companies are either valid or invalid
        # HINT: Must be an error in the ZMR if the identical request data for one company would achieve a different
        #       result for an other company.
        assert all(a['faulttext'] for a in responses) or not any(a['faulttext'] for a in responses), _(
            "Different BPK request results by company with identical request data! ZMR error?")

        return responses

    @api.model
    def response_ok(self, responses):
        if len(responses) >= 1 and not any(r['faulttext'] for r in responses):
            return True
        else:
            return False

    # MODEL ACTIONS
    @api.model
    def request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str()):
        """
        Wrapper for _request_bpk() that will additionally clean names and tries the request multiple times
        with different values depending on the request error
        :param firstname:
        :param lastname:
        :param birthdate:
        :param zipcode:
        :return: list(), Containing one result-dict for every company found
                         (at least one result is always in the list ELSE it would throw an exception)
        """
        # CHECK INPUT DATA
        if not all((firstname, lastname, birthdate)):
            raise ValueError(_("Firstname, Lastname and Birthdate are needed for a BPK request!"))

        # firstname cleanup
        firstname = clean_name(firstname, split=True)
        assert firstname, _("Firstname is empty after cleanup!")

        # lstname cleanup
        lastname = clean_name(lastname, split=False)
        assert lastname, _("Lastname is empty after cleanup!")

        # REQUEST BPK FOR EVERY COMPANY
        # HINT: _request_bpk() will always return at least one result or it would raise an exception
        responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate)

        # RETURN VALID BPK OR RETRY ON ERROR
        # ----------------------------------
        # 1.) Return the List of valid Responses(s)
        if self.response_ok(responses):
            return responses

        # 2.) Error: Person not found: Retry with birth-year only
        faultcode = responses[0].get('faultcode', "")
        year = False
        if 'F230' in faultcode:
            try:
                date = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
                year = date.strftime("%Y")
            except:
                try:
                    year = str(birthdate).split("-", 1)[0]
                except:
                    year = None
            if year:
                responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate=year)
                # Return list of valid responses
                if self.response_ok(responses):
                    return responses

        # 3.) Error: Multiple Persons found: Last retry with regular birthdate but add zipcode
        faultcode = responses[0].get('faultcode', "")
        if zipcode and any(code in faultcode for code in ('F231', 'F233')):
            birthdate = year or birthdate
            responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate,
                                          zipcode=zipcode)

        return responses

    @api.model
    def check_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str()):
        try:
            responses = self.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate, zipcode=zipcode)
            check_response = self.response_ok(responses)
            return check_response
        except Exception as e:
            logger.error(_("Exception in fso_con_zmr check_bpk():\n%s\n") % e)
            return False

    # --------------
    # RECORD ACTIONS
    # --------------
    @api.multi
    def set_bpk(self):
        """
        Creates or Updates BPK request for the given partner recordset (=BPKRequestIDS)

        HINT: Runs request_bpk() for every partner.
              Exception text will be written to BPKRequestError if request_bpk() raises one

        ATTENTION: Will also update partner fields: BPKRequestNeeded, LastBPKRequest, BPKRequestError

        :return: dict, partner id and relatet error if any was found
        """
        # TODO: set/unset and honor BPKRequestInProgress

        # TODO: Stop with an assertion if no company with complete access data can be found or the
        #       configuration of the request URL is not correct

        # Helper Method: Final partner update
        def finish_partner(partner,
                           bpk_request_error=None,
                           last_bpk_request=fields.datetime.now()):
            partner.BPKRequestNeeded = None
            partner.LastBPKRequest = last_bpk_request
            partner.BPKRequestError = bpk_request_error

        # ERROR DICTIONARY
        # HINT: Could be used for user messages in FS-Online
        errors = dict()

        # BPK REQUEST FOR EACH PARTNER
        # ----------------------------
        start_time = time.time()
        faulttext = None
        for p in self:

            # Check for donation_deduction_optout_web
            if p.donation_deduction_optout_web:
                errors[p.id] = _("%s (ID %s): Donation Deduction Opt Out is set!") % (p.name, p.id)
                finish_partner(p, bpk_request_error=errors[p.id])
                continue

            # Set BPK Request Data
            firstname, lastname, birthdate_web, zipcode = p.firstname, p.lastname, p.birthdate_web, p.zip
            if any(p[forced_field] for forced_field in self._bpk_forced_fields()):
                firstname = p.BPKForcedFirstname
                lastname = p.BPKForcedLastname
                birthdate_web = p.BPKForcedBirthdate
                zipcode = p.BPKForcedZip

            # BPK request
            try:
                start_time = time.time()
                resp = self.request_bpk(firstname=firstname, lastname=lastname, birthdate_web=birthdate_web,
                                        zipcode=zipcode)
                assert resp, _("%s (ID %s): No BPK-Request responses!")
            except Exception as e:
                errors[p.id] = _("%s (ID %s): BPK-Request exception: %s") % (p.name, p.id, e)
                finish_partner(p, bpk_request_error=errors[p.id])
                continue

            # Create or update BPK Requests from responses
            # ---
            for r in resp:
                faulttext = None

                # Prepare values for the bpk_request record
                values = {
                    'BPKRequestCompanyID': r['company_id'] or False,
                    'BPKRequestPartnerID': p.id or False,
                    'LastBPKRequest': fields.datetime.now(),
                }
                try:
                    response_time = float(r['response_time_sec'])
                except:
                    response_time = float()
                if r.get('private_bpk') and r.get('public_bpk'):
                    values.update({
                        'BPKPrivate': r.get('private_bpk') or False,
                        'BPKPublic': r.get('public_bpk') or False,
                        'BPKRequestDate': r.get('request_date') or False,
                        'BPKRequestURL': r.get('request_url') or False,
                        'BPKRequestData': r.get('request_data') or False,
                        'BPKRequestFirstname': firstname or False,
                        'BPKRequestLastname': lastname or False,
                        'BPKRequestBirthdate': birthdate_web or False,
                        'BPKRequestZIP': zipcode or False,
                        'BPKResponseData': r.get('response_content') or False,
                        'BPKResponseTime': response_time,
                    })

                else:
                    faulttext = r['faulttext'] or False
                    values.update({
                        'BPKErrorCode': r.get('faultcode') or False,
                        'BPKErrorText': faulttext,
                        'BPKErrorRequestDate': r.get('request_date') or False,
                        'BPKErrorRequestURL': r.get('request_url') or False,
                        'BPKErrorRequestData': r.get('request_data') or False,
                        'BPKErrorRequestFirstname': firstname or False,
                        'BPKErrorRequestLastname': lastname or False,
                        'BPKErrorRequestBirthdate': birthdate_web or False,
                        'BPKErrorRequestZIP': zipcode or False,
                        'BPKErrorResponseData': r.get('response_content') or False,
                        'BPKErrorResponseTime': response_time,
                    })

                # Search for existing res.partner.bpk records
                bpk = self.env['res.partner.bpk'].sudo().search([('BPKRequestCompanyID.id', '=', r['company_id']),
                                                                 ('BPKRequestPartnerID.id', '=', p.id)])
                # ATTENTION: Delete all but one res.partner.bpk record if there is more than one record per company
                # HINT: Only one bpk record per partner per company is allowed. If there is more than one we can
                #       be sure this is an error. It was most likely an concurrent request update after a sync from FS
                if len(bpk) > 1:
                    try:
                        # TODO: Unlink only unneded bpk records keep the newest valid one or if no request is valid
                        #       just the newest one
                        #       keep the
                        bpk.unlink()
                        bpk = None
                    except Exception as e:
                        errors[p.id] = _("%s (ID %s): More than one BPK record per company found "
                                         "and removal of BPK records failed also: %s") % (p.name, p.id, e)
                        finish_partner(p, bpk_request_error=errors[p.id])
                        # Finish this partner instead of continuing with the next bpk result if any
                        break

                # Create or update bpk records
                if bpk:
                    bpk = bpk.write(values)
                else:
                    bpk = self.env['res.partner.bpk'].sudo().create(values)
                # ---
                # END: Create or update BPK Requests from responses

            # Finish the partner
            # HINT: We use the faulttext from the last bpk request for this partner
            #       This should be no problem since all faulttexts must be identical if any exits at all
            finish_partner(p, bpk_request_error=faulttext)

        # Log runtime and error dictionary
        logger.info("set_bpk(): Processed %s partners in %.3f seconds" % (len(self), time.time()-start_time))
        if errors:
            logger.warning("set_bpk(): Partners with errors: \n%s\n\n" % pp.pprint(errors))

        # Return error dict
        # HINT: An empty dict() means no errors where found!
        return errors

    # --------------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED BPK PROCESSING
    # --------------------------------------------
    @api.model
    def find_bpk_partners_to_update(self,
                                    quick_search=True,
                                    limit=1,
                                    order='BPKRequestNeeded DESC, write_date DESC',
                                    fs_skip_partner_with_bpk_records=False,
                                    fs_in_progress_limit=48,
                                    fs_batch_size=10000):
        """
        # HINT: LIFO: As an optimization we reverse the order to latest first because it is very likely that we want the 
        #       latest updated records to be processed first and also that these records would most likely have relevant
        #       changes. In the circumstance that there is not enough time to process all bpk records the oldest ones
        #       would never be processed but this is just as bad or even worse as that youngest ones will never be
        #       processed.
        #
        :return: res.partner recordset
        """
        # ============
        # QUICK SEARCH
        # ============
        # Used by the method scheduled_set_bpk() which is normally started every minute by a scheduled
        # server action created by xml
        #
        # HINT: "donation_deduction_optout_web" and "BPKRequestInProgress" are checked by set_bpk() so we do not
        #       need to check it here also. If there are already false positives they will be clean after set_bpk()

        if quick_search:
            # Search for partners where BPKRequestNeeded is set
            domain = [('BPKRequestNeeded', '!=', False)]

            # Only search for res.partner with no existing bpk records
            # HINT: This may be useful if you want to process partners with no existing bpk records first
            if fs_skip_partner_with_bpk_records:
                domain = [('BPKRequestIDS', '=', False)] + domain

            # Return any found partners up to the set limit in LIFO (LastIn FirstOut) order
            # HINT: This means that records with the latest (newest) BPKRequestNeeded datetime will be the first in
            #       the recordset
            partners_to_update = self.env['res.partner'].search(domain, limit=limit, order=order)
            return partners_to_update

        # ===========
        # FULL SEARCH
        # ===========
        # The goal of the full search is to find any partner that would need an BPK request but BPKRequestNeeded
        # is not set. This may be because a new company was added or an existing company was removed or caused by
        # sosync errors.
        #
        # HINT: Used by check_bpk_request_needed() which is normally started once a week by a scheduled server action
        #       created by xml.

        # Start with an empty record set
        partners_to_update = self.env['res.partner']

        # Find all companies with fully filled ZMR access fields
        try:
            companies = self._find_bpk_companies()
            assert companies, _("BPK full search: No company found with complete Austrian ZMR access data!")
        except Exception as e:
            logger.error(_("BPK full search: Exception while searching for companies with complete ZMR "
                           "settings:\n%s\n") % e)
            return partners_to_update

        # BASIC SEARCH DOMAIN PARTS
        # ATTENTION: Char Fields (and ONLY Char fields) in odoo domains should be checked with '(not) in', [False, '']
        #            Because the sosyncer v1 may wrote empty strings "" to Char fields instead of False or None
        #
        # Only search for partners
        #     - with donation_deduction_optout_web not set
        #     - with BPKRequestNeeded NOT set
        #     - with full set of regular fields OR full set of forced fields
        #     - where no BPK request is in progress or the BPK request processing start is far in the past or future
        # TODO: !!! Test and debug this search domain !!!
        base_domain = [
            '&', '&', '&',
            ('donation_deduction_optout_web', '=', False),
            ('BPKRequestNeeded', '=', False),
            '|',
              '&', '&',
              ('firstname', 'not in', [False, '']),
              ('lastname', 'not in', [False, '']),
              ('birthdate_web', '!=', False),

              '&', '&',
              ('BPKForcedFirstname', 'not in', [False, '']),
              ('BPKForcedLastname', 'not in', [False, '']),
              ('BPKForcedBirthdate', '!=', False),
            '|', '|',
              ('BPKRequestInProgress', '=', False),
              ('BPKRequestInProgress', '<', str(fields.datetime.now() - timedelta(hours=fs_in_progress_limit))),
              ('BPKRequestInProgress', '>', str(fields.datetime.now() + timedelta(hours=fs_in_progress_limit)))
            ]

        # A.) FIND PARTNERS TO UPDATE WITH NO BPK RECORDS
        # -----------------------------------------------
        logger.info("find_bpk_partners_to_update(): A.) FIND PARTNERS WITH NO BPK RECORDS FIRST")

        # Create search domain for partners with no existing BPK records
        domain = [('BPKRequestIDS', '=', False)] + base_domain
        logger.info("Search domain for partners with no BPK records: %s" % domain)

        # Search for partners with no existing BPK records
        partner_without_bpks = self.env['res.partner'].search(domain, order=order, limit=limit)
        logger.info("Found %s partners without existing BPK records." % len(partner_without_bpks))

        # Return recordset if limit is already reached or continue to next step
        if fs_skip_partner_with_bpk_records or (limit and len(partner_without_bpks) >= limit):
            return partner_without_bpks

        # B.) FIND AND CHECK PARTNERS TO UPDATE WITH EXISTING BPK RECORDS
        # ---------------------------------------------------------------
        # - Find only partners that fulfill the minimum requirements for a bpk check
        # - Check if latest bpk request data and current partner data are identical
        # HINT: if fs_skip_partner_with_bpk_records is set this would be never reached! See A.)
        # ATTENTION: This will at some point run for all partners with BPK records so make sure to run the full search
        #            without "fs_skip_partner_with_bpk_records" not too often e.g.: only once a week
        logger.info("find_bpk_partners_to_update(): B.) FIND AND CHECK PARTNERS TO UPDATE WITH BPK RECORDS")

        # Use partner_without_bpks as the starting point
        partners_to_update = partner_without_bpks

        # Create search domain for partners with existing BPK records
        domain = [('BPKRequestIDS', '!=', False)] + base_domain
        logger.info("Search domain for partners with BPK records: %s" % domain)

        # Search check partners with bpk requests in batches of 10000
        # ATTENTION: To load one million res.partner from database to memory takes approximately 30 seconds
        # HINT: remaining -1 means No Limit = Check all partners with bpk records
        # TODO: TEST THIS while loop
        offset = 0
        remaining = -1 if not limit else limit - len(partner_without_bpks)
        while remaining:

            # Search for partners
            partner_with_bpks = self.env['res.partner'].search(domain, order=order, limit=fs_batch_size, offset=offset)
            if not partner_with_bpks:
                logger.info("No partners left to check with existing bpk records!")
                # Exit while loop
                break
            logger.info("Start first batch of %s parnters to check for BPKRequestNeeded" % len(partner_with_bpks))

            # Check partners in batches
            for p in partner_with_bpks:
                # Stop to check for other partners if remaining (=limit) is already reached!
                if remaining == 0:
                    # Exit partner for loop which will then end the while loop cause remaining = 0
                    break

                # B.1.) Check if there are missing or too many BPK request for companies with full zmr access data
                bpk_company_ids = [r.BPKRequestCompanyID.id for r in p.BPKRequestIDS]

                # Check if the partner has bpk request records connected to companies that are non existing
                # or without complete ZMR header data.
                # ATTENTION: We will not delete them but just log them! Also they will not be deleted in set_bpk()
                #            This is a safety net if someone accidentally deleted access data of a company or a company
                # HINT: s - t = new set with elements in s but not in t
                orphan_records = set(bpk_company_ids) - set(companies.ids)
                if orphan_records:
                    logger.error(_("BPK Records %s found for non existing companies "
                                   "or companies where the ZMR BPK access data was removed "
                                   "for partner %s: %s %s") % (orphan_records, p.id, p.firstname, p.lastname))

                # Check if any bpk records are missing for a company and if so add it to partners_to_update
                # HINT: s - t = new set with elements in s but not in t
                if set(companies.ids) - set(bpk_company_ids):
                    partners_to_update = partners_to_update | p
                    remaining = remaining - 1
                    continue

                # TODO: Check if there is more than one bpk record per company per partner
                #       If so add it to partners_to_update and continue to next partner
                # HINT: set_bpk() will clean the unnecessaery bpk records()

                # B.2.) Check if in any BPK request the bpk request data neither for regular nor for error request
                #       fields matches the current request data.
                #       HINT: Forced BPK fields takes precedence
                #       ATTENTION: False == u'' will resolve to False! Therefore we use (False or '') == ...
                for r in p.BPKRequestIDS:
                    # Only check non orphan bpk records: ... in companies.ids
                    if r.BPKRequestCompanyID.id in companies.ids and (
                        not (((p.BPKForcedFirstname or p.firstname or '') == (r.BPKRequestFirstname or '') and
                              (p.BPKForcedLastname or p.lastname or '') == (r.BPKRequestLastname or '') and
                              (p.BPKForcedBirthdate or p.birthdate_web or '') == (r.BPKRequestBirthdate or '')
                              )
                             or
                             ((p.BPKForcedFirstname or p.firstname or '') == (r.BPKErrorRequestFirstname or '') and
                              (p.BPKForcedLastname or p.lastname or '') == (r.BPKErrorRequestLastname or '') and
                              (p.BPKForcedBirthdate or p.birthdate_web or '') == (r.BPKErrorRequestBirthdate or '')
                              )
                             )
                    ):
                        partners_to_update = partners_to_update | p
                        remaining = remaining - 1
                        # Do not check any other bpk requests if one with an error was already found
                        break

            # Create offset for next batch of partners to process
            offset += fs_batch_size

        # Sort the record set partners_to_update
        # TODO: Check if this is still needed
        sort_field = order.split(' ', 1)[0]
        reverse = False if order.endswith('ASC') else True
        partners_to_update = partners_to_update.sorted(key=lambda l: getattr(l, sort_field), reverse=reverse)

        # Return record set of partners where a BPK request is needed!
        logger.info(_("Full search: Total partners found requiring a BPK request: %s") % len(partners_to_update))
        return partners_to_update

    # TODO: !!! Rework this for new set_bpk() and new find_bpk_partners_to_update() !!!
    @api.model
    def scheduled_set_bpk(self, limit=1800):
        logger.info(_("Scheduled BPK fetching: START"))

        # Calculate the limit of partners to process based on job interval and interval type with 50% safety
        # which means a maximum number of processed partners of 24*60*60/4 = 21600 in 24 hours.
        # HINT: The number of BPK request could be much higher since every partner could cause multiple requests
        #       for multiple companies.
        interval_to_seconds = {
            "weeks": 7 * 24 * 60 * 60,
            "days": 24 * 60 * 60,
            "hours": 60 * 60,
            "minutes": 60,
            "seconds": 1
        }
        scheduled_action = self.env.ref('fso_con_zmr.ir_cron_scheduled_set_bpk')
        if scheduled_action and scheduled_action.interval_type in interval_to_seconds:
            limit = int(scheduled_action.interval_number * interval_to_seconds[scheduled_action.interval_type] / 4)
            # In case someone sets interval to one second
            limit = 1 if limit <= 0 else limit

        # Find Partners to create or update bpk records
        logger.info(_("Scheduled BPK fetching: Limit set to %s based on scheduler interval in seconds/4") % limit)
        partners_to_update = self.find_bpk_partners_to_update(limit=limit)

        # Set all partners to "BPK processing in progress" to avoid double calls
        # https://www.odoo.com/de_DE/forum/hilfe-1/question/how-to-get-a-new-cursor-on-new-api-on-thread-63441
        # HINT: Done in new Env to directly commit changes
        # HINT: You don't need close your cursors because it is closed after "with" ends
        # HINT: You don't need clear your caches because they are cleared when "with"  ends
        logger.warning("Scheduled BPK fetching: Set 'BPK request in process' in new environment")
        with openerp.api.Environment.manage():
            with openerp.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                self.with_env(new_env).browse(
                    partners_to_update.ids).write({'BPKRequestInProgress': fields.datetime.now()})
                new_env.cr.commit()  # Don't show an invalid-commit
                logger.warning("Scheduled BPK fetching: Set 'BPK request in process' DONE")

        # Run set_bpk() for the partners found
        # HINT: Done in new Env to avoid concurrent update exceptions because of write in former steps
        # HINT: You don't need close your cursors because it is closed after "with" ends
        # HINT: You don't need clear your caches because they are cleared when "with"  ends
        logger.info(_("Scheduled BPK fetching: Set or update BPK records for %s partner "
                      "in new environment") % len(partners_to_update))
        with openerp.api.Environment.manage():
            with openerp.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                # HINT: Do not raise exceptions in scheduled processing to make sure changes are written to all
                #       partners without an exception! (If an exception is raised cr is not committed in the end!)
                self.with_env(new_env).browse(partners_to_update.ids).set_bpk(raise_exceptions=False)
                new_env.cr.commit()  # Don't show an invalid-commit

        logger.info(_("Scheduled BPK fetching: DONE"))

    # TODO: !!! Rework this for new set_bpk() and new find_bpk_partners_to_update() !!!
    @api.model
    def check_bpk_request_needed(self):
        logger.info(_("Scheduled BPKRequestNeeded check: START"))
        partner = self.find_bpk_partners_to_update(limit=0,
                                                   full_search=True,
                                                   full_search_skip_bpk_request_needed=True)
        if partner:
            logger.warning(_("Scheduled BPKRequestNeeded check: "
                             "Set BPKRequestInProgress for %s partner") % len(partner))
            partner.write({'BPKRequestNeeded': fields.datetime.now(),
                           'BPKRequestInProgress': None})
        logger.info(_("Scheduled BPKRequestNeeded check: DONE"))

    @api.multi
    def tester(self):
        self.check_bpk_request_needed()
