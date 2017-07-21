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

    # BPK Fields for request processing and optimization and filtering
    BPKRequestInProgress = fields.Datetime(string="BPK Request in progress", readonly=True)
    BPKRequestNeeded = fields.Datetime(string="BPK Request needed", readonly=True)
    LastBPKRequest = fields.Datetime(string="Last BPK Request", readonly=True)
    # TODO optional: computed state field
    # HINT: colors="red:BPKRequestDate == False and BPKErrorRequestDate;
    #               orange:BPKRequestDate &lt; BPKErrorRequestDate;
    #               green:BPKRequestDate &gt; BPKErrorRequestDate"
    # HINT: This field shows only the state of the current bpk requests and does not check if current data is still
    # ATTENTION: Date fields are in char format - make sure greater than or lower than comparison works as expected
    # BPKRequestState = fields.Selection(
    #     selection=[('pending', 'Pending'),                    # BPKRequestNeeded is set
    #                ('found', 'Found'),                        # any(BPKRequestDate > BPKErrorRequestDate)
    #                ('found_outdated', 'Found but outdated'),  # any(BPKRequestDate < BPKErrorRequestDate)
    #                ('notfound', 'Not Found')],                # any(Not BPKRequestDate and BPKErrorRequestDate)
    #     string="BPK Request(s) State", compute=_compute_bpk_request_state, store=True)

    # Compute BPKRequestNeeded
    @api.multi
    def write(self, vals):
        """Override write to check for BPKRequestNeeded"""

        # Compute BPKRequestNeeded
        # HINT: Even if there is already a BPK-Request we can assume that if data changed the bpkrequest needs to be
        #       done again. This is not 100% exact this way but is fast and easy!!! Which i guess is more important.
        #       It could happen that there are false positives sometimes because we do not explicitly check for just the
        #       forced fields if they are set.
        _bpk_fields = ['firstname', 'lastname', 'birthdate_web', 'zip',
                       'BPKForcedFirstname', 'BPKForcedLastname', 'BPKForcedBirthdate']
        fields_to_check = [field for field in _bpk_fields if field in vals]
        # Create an empty recordset for res.partner to add found partners later
        partners_bpk_needed = self.env['res.partner']
        # If there is any bpk relevant field in vals we need to check the partner(s)
        if fields_to_check and 'BPKRequestNeeded' not in vals:
            for p in self:
                # If BPKRequestNeeded is already set we can skip this test
                if not p.BPKRequestNeeded and not p.donation_deduction_optout_web:
                    for field in fields_to_check:
                        if p[field] != vals[field]:
                            # Add the partners to the recordset
                            partners_bpk_needed = partners_bpk_needed | p
                            break
        # Update the partners
        if partners_bpk_needed:
            if partners_bpk_needed == self:
                vals['BPKRequestNeeded'] = fields.datetime.now()
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
        #            Because the sosyncer or the website may wrote empty strings "" to Char fields instead of False
        companies = self.env['res.company'].sudo().search([('stammzahl', 'not in', [False, '']),
                                                           ('pvpToken_userId', 'not in', [False, '']),
                                                           ('pvpToken_cn', 'not in', [False, '']),
                                                           ('pvpToken_crt_pem', '!=', False),
                                                           ('pvpToken_prvkey_pem', '!=', False),
                                                           ('BPKRequestURL', '!=', False)])
        # Assert that at least one company with complete data was found
        assert companies, _("No company with complete security header data found!")

        # Assert that all companies have the same BPKRequestURL Setting (Either test or live)
        if len(companies) > 1:
            request_url = companies[0].BPKRequestURL
            assert all((c.BPKRequestURL == request_url for c in companies)), _("All companies must use the same "
                                                                               "BPKRequestURL!")

        return companies

    def _request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str()):
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

                # TODO: Log Request attempts to database to throw an exception if daily max limit from ZMR is reached
                #       a new res.setting should be added for this as well as the needed field
                # TODO: Log request per minute to database to "delay" the request if max request per minute is reached
                #       a new res.setting should be added for this as well as the needed field
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
        if not all((firstname, lastname, birthdate)):
            raise ValueError(_("Firstname, Lastname and Birthdate are needed for a BPK request!"))

        # PROCESS FIRSTNAME
        firstname = clean_name(firstname, split=True)

        # PROCESS LASTNAME
        lastname = clean_name(lastname, split=False)

        # BPK REQUESTS
        responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate)

        # Valid Request or an empty list was returned
        if self.response_ok(responses) or len(responses) < 1:
            return responses

        # Person not found: retry with birth-year only
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
                # Valid Request or an empty list was returned
                if self.response_ok(responses) or len(responses) < 1:
                    return responses

        # Multiple Persons found: Retry with zipcode
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
    def set_bpk(self, raise_exceptions=True):
        partner = self
        error_messages = ""

        # Find partner with donation_deduction_optout_web set
        ddow = self.env['res.partner'].search(
            [('id', 'in', self.ids),
             ('donation_deduction_optout_web', '!=', False)])
        # Remove partner with donation_deduction_optout_web set
        if ddow:
            logger.warning(_("set_bpk(): Donation Deduction Opt Out is set for partner:\n%s\n "
                             "BPK check skipped for them!\n\n") % ddow.ids)
            partner = partner - ddow

        if not partner:
            raise Warning(_("set_bpk(): No partner left after excluding partners with "
                            "Donation Deduction Opt Out set!"))

        # ATTENTION: Do NOT exclude partners with "request in progress" here otherwise "request in progress" would
        #            never be cleared in some situations!

        # Process BPK-Requests per partner
        start_time = time.time()
        processed_partner_count = 0
        for p in partner:
            responses = []
            err_msg = ""

            # PREPARE REQUEST VALUES
            firstname = p.firstname
            lastname = p.lastname
            birthdate_web = p.birthdate_web
            zipcode = p.zip
            if p.BPKForcedFirstname or p.BPKForcedLastname or p.BPKForcedBirthdate:
                # Check for complete set of Force-BPK-Fields
                if not all((p.BPKForcedFirstname, p.BPKForcedLastname, p.BPKForcedBirthdate)):
                    err_msg = _("set_bpk(): Forced BPK Fields are not completely set for partner %s %s with id %s! "
                                "BPK check skipped!\n\n") % (p.firstname, p.lastname, p.id)

                # Overwrite BPK request data with forced settings
                firstname = p.BPKForcedFirstname
                lastname = p.BPKForcedLastname
                birthdate_web = p.BPKForcedBirthdate

            # REQUEST BPK(s)
            # HINT: For every res.company with complete pvpToken header data
            if not err_msg:
                try:
                    responses = p.request_bpk(firstname=firstname, lastname=lastname,
                                              birthdate=birthdate_web, zipcode=zipcode)
                except Exception as e:
                    err_msg = _("set_bpk(): request_bpk() exception for partner "
                                "%s: %s %s\n%s\n") % (p.id, p.firstname, p.lastname, e)
                    logger.warning(err_msg)
                    error_messages += err_msg

            # HANDLE EXCEPTIONS
            # HINT: If we have any exception at this point we need to "fake" the responses list to still update or
            #       create the BPK requests of the partner so that they will no longer be in the BPKRequestNeeded list
            #       after an check_bpk_request_needed() run!
            if err_msg:
                logger.warning(err_msg)
                error_messages += err_msg
                # Fake responses
                companies = self._find_bpk_companies()
                for c in companies:
                    responses.append({'company_id': c.id, 'faulttext': err_msg})

            # CREATE OR UPDATE 'res.partner.bpk' RECORDS
            last_bpkrequest_date = fields.datetime.now() + timedelta(seconds=1)
            for r in responses:
                values = {
                    'BPKRequestCompanyID': r['company_id'] or False,
                    'BPKRequestPartnerID': p.id or False,
                    'LastBPKRequest': last_bpkrequest_date,
                }
                try:
                    response_time = float(r['response_time_sec'])
                except:
                    response_time = float()
                # Process the response and transform it to a dict to create or update an res.partner.bpk record
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
                    values.update({
                        'BPKErrorCode': r.get('faultcode') or False,
                        'BPKErrorText': r['faulttext'] or False,
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

                # Create new or update existing BPK record
                bpk = self.env['res.partner.bpk'].sudo().search([('BPKRequestCompanyID.id', '=', r['company_id']),
                                                                 ('BPKRequestPartnerID.id', '=', p.id)])
                assert len(bpk) <= 1, _("set_bpk(): More than one BPK-Request record found per company! "
                                        "Partner %s: %s %s Company: %s") % (p.id, p.firstname, p.lastname,
                                                                            r['company_id'])
                if bpk:
                    bpk.write(values)
                else:
                    self.env['res.partner.bpk'].sudo().create(values)

            # FINISH PARTNER
            # HINT: We add one seconds of safety to LastBPKRequest Date to avoid conflicts with write_date in domains
            p.write({'BPKRequestInProgress': None,
                     'BPKRequestNeeded': None,
                     'LastBPKRequest': last_bpkrequest_date})
            processed_partner_count = processed_partner_count + 1

        # Log result
        runtime = time.time() - start_time
        logger.info("set_bpk(): processed_partner_count: %s in %.3f seconds" % (processed_partner_count, runtime))

        # Raise warning exception if any warning_messages exits
        if error_messages:
            logger.warning(_("set_bpk(): Exceptions:\n%s") % error_messages)
            if raise_exceptions:
                raise Warning(error_messages)

    # --------------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED BPK PROCESSING
    # --------------------------------------------
    @api.model
    def find_bpk_partners_to_update(self, limit=1, order='write_date DESC', skip_no_bpk=False, in_progress_limit=48,
                                    full_search=False, full_search_skip_bpk_request_needed=False, batch=10000):
        """
        # HINT: LIFO: As an optimization we reverse the order to latest first because it is very likely that we want the 
        #       latest updated records to be processed first and also that these records would most likely have relevant
        #       changes. In the circumstance that there is not enough time to process all bpk records the oldest ones
        #       would never be processed but this is just as bad or even worse as that youngest ones will never be
        #       processed.
        #
        :param full_search: bool # If True ignore BPKRequestNeeded and do a full search
        :param full_search_skip_bpk_request_needed: bool # Do not search (and therefore return) partners with 
                                                           BPKRequestNeeded = True
        :param skip_no_bpk: bool # Do not check for res.partner without bpk requests
        :param in_progress_limit: int # ignore BPKRequestInProgress if older than x hours
        :param limit: int # maximum quantity of partners to process, use 0 or None for no limit!
        :param order: char # field to sort by and sort order (DESC or ASC) e.g.: 'write_date ASC' 
                             ASC=regular DESC=reverse for .sorted() record set operation
                             ASC on date fields means oldest first (Ascend from oldest date to newest date)
                             DESC on date fields means newest first (Descend from newest date to oldest date)

        :param batch: int # Batch size for the processing of partners with bpk records.
                            This is useful for memory / speed optimization
        :return: recordset # res.partner
        """
        # Common Search-Domain-Parts
        # ATTENTION: Char Fields (and ONLY Char fields) in odoo domains should be checked with '(not) in', [False, '']
        #            Because the sosyncer or the website may wrote empty strings "" to Char fields instead of False
        # HINT: Include partners in search result if BPKRequestInProgress is False or older or newer(=future) than
        #       now+in_progress_limit
        # TODO: Add the FORCED FIELDS AS AN "OR" TO THE REGULAR FIELDS
        domain = [('donation_deduction_optout_web', '=', False),
                  ('firstname', 'not in', [False, '']),
                  ('lastname', 'not in', [False, '']),
                  ('birthdate_web', '!=', False),
                  '|', '|',
                      ('BPKRequestInProgress', '=', False),
                      ('BPKRequestInProgress', '<', str(fields.datetime.now() -
                                                        timedelta(hours=in_progress_limit))),
                      ('BPKRequestInProgress', '>', str(fields.datetime.now() +
                                                        timedelta(hours=in_progress_limit)))
                  ]

        # REGULAR SEARCH
        # --------------
        # Searches for all partners where BPKRequestNeeded is set that are not already in processing
        if not full_search:
            domain = [('BPKRequestNeeded', '!=', False),] + domain
            if skip_no_bpk:
                # Search only for partners with existing BPK records
                domain = [('BPKRequestIDS', '!=', False)] + domain
            partners_to_update = self.env['res.partner'].search(domain, limit=limit, order=order)
            return partners_to_update

        # FULL SEARCH
        # -----------
        # Do a full search for all partners and return any partner where a BPK request is needed

        # Exclude partners with BPKRequestNeeded = True if full_search_skip_bpk_request_needed is set
        # HINT: This is only useful to speed up cleanup runs.
        if full_search_skip_bpk_request_needed:
            domain = [('BPKRequestNeeded', '=', False)] + domain

        # Start with an empty record set
        partners_to_update = self.env['res.partner']

        # Find all companies with fully filled ZMR access fields
        try:
            companies = self._find_bpk_companies()
        except Exception as e:
            logger.error(_("_find_bpk_partners(): Exception while fetching companies:\n%s\n") % e)
            return partners_to_update

        # 1.) CHECK PARTNERS WITH NO BPK RECORDS
        partner_without_bpks = list()
        if not skip_no_bpk:
            no_bpk_domain = [('BPKRequestIDS', '=', False)] + domain
            logger.info("Full search: Find partners without BPK records: %s" % no_bpk_domain)
            partner_without_bpks = self.env['res.partner'].search(no_bpk_domain, order=order, limit=limit)
            logger.info("Full search: Found partners without BPK records: %s" % len(partner_without_bpks))
            # Return if we have already enough partners found
            if limit and len(partner_without_bpks) >= limit:
                return partner_without_bpks
            else:
                partners_to_update = partners_to_update | partner_without_bpks

        # 2.) CHECK PARTNERS WITH EXISTING BPK RECORDS
        #     HINT: Must use all partners without limit for further checks!
        #     HINT: To load 1.000.000 res.partner from database to memory takes approximately 30 seconds
        #     HINT: remaining -1 means No Limit = Find all partners with bpks to update
        offset = 0
        remaining = -1 if not limit else limit - len(partner_without_bpks)
        bpk_domain = [('BPKRequestIDS', '!=', False)] + domain
        logger.info("Full search: Find partners to check with existing BPK records: %s" % bpk_domain)
        while remaining:
            # TODO: Maybe we could write an sql select that mimics the logic of the full search pyhton code without
            #       cycling through the partners
            # http://stackoverflow.com/questions/27346751/openerp-domain-filters-how-to-compare-2-fields-in-object
            partner_with_bpks = self.env['res.partner'].search(bpk_domain, order=order, limit=batch, offset=offset)
            logger.info("Full search: Found partners to check with existing BPK records: %s"
                        % len(partner_with_bpks))
            offset = offset + batch
            for p in partner_with_bpks:
                # Stop if enough partners are found
                if remaining == 0:
                    break

                # 2.1.) Check if there are missing or too many BPK request
                bpk_company_ids = [r.BPKRequestCompanyID.id for r in p.BPKRequestIDS]

                # Check if the partner has bpk request records connected to companies that are non existing
                # or without complete ZMR header data.
                # HINT: This is just a warning in the log - we do currently not delete the bpk records to avoid
                #       deleting bpk request records if someone just temporarily removes ZMR data from a company
                #       Maybe we should set these records to active = False ...
                # HINT: s - t = new set with elements in s but not in t
                orphan_records = set(bpk_company_ids) - set(companies.ids)
                if orphan_records:
                    logger.error(_("Full Search: BPK Records %s found for non existing companies "
                                   "or companies where the ZMR BPK access data was removed "
                                   "for partner %s: %s %s") % (orphan_records, p.id, p.firstname, p.lastname))

                # Check if any bpk records are missing for a company and if so add it to partners_to_update
                # HINT: s - t = new set with elements in s but not in t
                if set(companies.ids) - set(bpk_company_ids):
                    partners_to_update = partners_to_update | p
                    remaining = remaining - 1
                    continue

                # 2.2.) Check if in any BPK request the bpk request data neither for regular nor for error request
                #       fields matches the current request data.
                #       HINT: Forced BPK fields takes precedence
                #       ATTENTION: False == u'' will resolve to False! Therefore we use (False or '') == ...
                for r in p.BPKRequestIDS:
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
                        break

            # Stop while loop if no partners are left to check
            remaining = None

        # Finally sort the record set partners_to_update
        sort_field = order.split(' ', 1)[0]
        reverse = False if order.endswith('ASC') else True
        partners_to_update = partners_to_update.sorted(key=lambda l: getattr(l, sort_field), reverse=reverse)

        # Return record set of partners to update
        logger.info(_("Full search: Total partners found requiring a BPK request: %s") % len(partners_to_update))
        return partners_to_update

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
