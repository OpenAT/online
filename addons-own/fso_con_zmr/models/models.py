# -*- coding: utf-8 -*-
import os
import errno
from os.path import join as pj
from openerp import api, models, fields
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.soap import soap_request
from lxml import etree
import requests
import time
import logging
import datetime
from openerp.tools import config

logger = logging.getLogger(__name__)


class CompanyAustrianZMRSettings(models.Model):
    _inherit = 'res.company'

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


class ResPartnerZMRGetBPK(models.Model):
    _inherit = 'res.partner'

    # FIELDS
    # BPK forced request values
    BPKForcedFirstname = fields.Char(string="BPK Forced Firstname")
    BPKForcedLastname = fields.Char(string="BPK Forced Lastname")
    BPKForcedBirthdate = fields.Date(string="BPK Forced Birthdate")

    # Successful BPK request
    # This set of fields gets only updated if private and public bpk was returned successfully
    BPKPrivate = fields.Char(string="BPK Private", readonly=True)
    BPKPublic = fields.Char(string="BPK Public", readonly=True)

    BPKRequestDate = fields.Datetime(string="BPK Request Date", readonly=True)
    BPKRequestData = fields.Text(string="BPK Request Data", readonly=True)
    BPKRequestFirstname = fields.Char(string="BPK Request Firstname", readonly=True)
    BPKRequestLastname = fields.Char(string="BPK Request Lastname", readonly=True)
    BPKRequestBirthdate = fields.Date(string="BPK Request Birthdate", readonly=True)

    BPKResponseData = fields.Text(string="BPK Response Data", readonly=True)
    BPKResponseTime = fields.Float(string="BPK Response Time", readonly=True)


    # Invalid BPK request
    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    BPKErrorCode = fields.Char(string="BPK-Error Code", readonly=True)
    BPKErrorText = fields.Text(string="BPK-Error Text", readonly=True)

    BPKErrorRequestDate = fields.Datetime(string="BPK-Error Request Date", readonly=True)
    BPKErrorRequestData = fields.Text(string="BPK-Error Request Data", readonly=True)
    BPKErrorRequestFirstname = fields.Char(string="BPK-Error Request Firstname", readonly=True)
    BPKErrorRequestLastname = fields.Char(string="BPK-Error Request Lastname", readonly=True)
    BPKErrorRequestBirthdate = fields.Date(string="BPK-Error Request Birthdate", readonly=True)

    BPKErrorResponseData = fields.Text(string="BPK-Error Response Data", readonly=True)
    BPKErrorResponseTime = fields.Float(string="BPK-Error Response Time", readonly=True)


    # MODEL ACTIONS
    @api.model
    def request_bpk(self, firstname=str(), lastname=str(), birthdate=str()):
        result = {'organization': "", 'request_data': "", 'request_url': "",
                  'response_http_error_code': "", 'response_content': "", 'response_time_sec': "",
                  'private_bpk': "", 'public_bpk': "", 'faultcode': "", 'faulttext': ""
                  }

        # Validate input
        if not all((firstname, lastname, birthdate)):
            raise ValidationError, _("Missing parameter! Mandatory are firstname, lastname and birthdate!")

        # Get the request_data_template path
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                      % soaprequest_templates
        getbpk_template = pj(soaprequest_templates, 'GetBPK_j2template.xml')
        assert os.path.exists(soaprequest_templates), _("GetBPK_j2template.xml not found at %s") \
                                                      % getbpk_template

        # Get current users company
        cmp = self.env.user.company_id
        result['organization'] = cmp.name

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

        # TODO: Log Request attempt
        start_time = time.time()
        response = soap_request(url="https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR",
                                template=getbpk_template,
                                crt_pem=cmp.pvpToken_crt_pem_path, prvkey_pem=cmp.pvpToken_prvkey_pem_path,
                                pvpToken={
                                    "authorize": {
                                        "role": ""
                                    },
                                    "authenticate": {
                                        "userPrincipal": {
                                            "cn": cmp.pvpToken_cn,
                                            "gvGid": "AT:VKZ:" + cmp.stammzahl,
                                            "userId": cmp.pvpToken_userId,
                                            "gvOuId": cmp.pvpToken_gvOuId,
                                            "gvSecClass": "2",
                                            "ou": cmp.pvpToken_ou
                                        },
                                        "participantId": "AT:VKZ:" + cmp.stammzahl
                                    }
                                },
                                GetBPK={
                                    "VKZ": cmp.stammzahl,
                                    "Target": {
                                        "BereichsKennung": "urn:publicid:gv.at:cdid+SA",
                                        "VKZ": "BMF"
                                    },
                                    "ListMultiplePersons": "",
                                    "InsertERnP": "",
                                    "PersonInfo": {
                                        "AuskunftssperreGesetzt": "",
                                        "TravelDocument": {
                                            "IssuingCountry": "",
                                            "DocumentNumber": "",
                                            "IssuingAuthority": "",
                                            "IssueDate": "",
                                            "DocumentType": ""
                                        },
                                        "RegularDomicile": {
                                            "Locality": "",
                                            "Municipality": "",
                                            "StateCode3": "",
                                            "DeliveryAddress": {
                                                "DoorNumber": "",
                                                "Unit": "",
                                                "AddressLine": "",
                                                "StreetName": "",
                                                "BuildingNumber": ""
                                            },
                                            "PostalCode": "",
                                            "HistoricRecord": ""
                                        },
                                        "Person": {
                                            "Name": {
                                                "GivenName": firstname,
                                                "PrefixedDegree": "",
                                                "SuffixedDegree": "",
                                                "FamilyName": lastname
                                            },
                                            "AlternativeName": {
                                                "FamilyName": ""
                                            },
                                            "Sex": "",
                                            "DateOfBirth": birthdate,
                                            "Identification": {
                                                "Type": "",
                                                "Value": ""
                                            },
                                            "Nationality": "",
                                            "PlaceOfBirth": "",
                                            "CountryOfBirth": ""
                                        },
                                        "DateOfBirthWildcard": "",
                                        "AddressCodes": {
                                            "ADRCD": "",
                                            "OBJNR": "",
                                            "NTZLNR": "",
                                            "OKZ": "",
                                            "SKZ": "",
                                            "SUBCD": "",
                                            "GKZ": ""
                                        }
                                    },
                                    "BereichsKennung": "urn:publicid:gv.at:wbpk+" + cmp.stammzahl.replace('-', '+')
                                },
                                )
        assert response.content, _("GetBPK-Request response has no content!")
        result['request_data'] = response.request.body
        result['request_url'] = response.request.url
        response_time = time.time() - start_time
        result['response_time_sec'] = "%.3f" % response_time
        result['response_content'] = response.content
        # Todo: Log Request status (success, error and request time)

        # Process soap xml answer
        parser = etree.XMLParser(remove_blank_text=True)
        response_etree = etree.fromstring(response.content, parser=parser)
        response_pprint = etree.tostring(response_etree, pretty_print=True)

        # Validate xml response
        if response.status_code != requests.codes.ok:
            result['response_http_error_code'] = response.status_code
            error_code = response_etree.find(".//faultcode")
            result['faultcode'] = error_code.text if error_code is not None else result['faultcode']
            error_text = response_etree.find(".//faultstring")
            result['faulttext'] = error_text.text if error_text is not None else result['faulttext']
            return result

        # Extract BPKs
        private_bpk = response_etree.find(".//GetBPKReturn")
        result['private_bpk'] = private_bpk.text if private_bpk is not None else result['private_bpk']
        public_bpk = response_etree.find(".//FremdBPK")
        result['public_bpk'] = public_bpk.text if public_bpk is not None else result['public_bpk']

        return result

    # ACTIONS
    @api.multi
    def set_bpk(self):
        for p in self:
            request_datetime = datetime.datetime.now()

            # Try to request a BPK
            try:
                result = p.request_bpk(firstname=p.firstname, lastname=p.lastname, birthdate=p.birthdate_web)
            except Exception as e:
                # The request failed with an assertion. It is very likely that we have no request or response data
                p.BPKErrorCode = ""
                p.BPKErrorText = ""
                p.BPKErrorRequestDate = request_datetime
                p.BPKErrorRequestData = ""
                p.BPKErrorResponseData = _("BPK Request Assertion:\n\n%s\n") % e
                p.BPKErrorResponseTime = None
                # If we have only one partner to check stop execution and return a warning
                if self.ensure_one():
                    return {"warning": _("BPK Request Error:\n%s\n") % e}

            # Store the result of the BPK request
            # request_bpk returned a valid and complete result
            if not result['response_http_error_code'] and result['private_bpk'] and result['public_bpk']:
                p.BPKPrivate = result['private_bpk']
                p.BPKPublic = result['public_bpk']
                p.BPKRequestDate = request_datetime
                p.BPKRequestData = result['request_data']
                p.BPKResponseData = result['response_content']
                p.BPKResponseTime = float(result['response_time_sec'])
            # request_bpk returned an error or an incomplete answer
            else:
                p.BPKErrorCode = result['faultcode']
                p.BPKErrorText = result['faulttext']
                p.BPKErrorRequestDate = request_datetime
                p.BPKErrorRequestData = result['request_data']
                p.BPKErrorResponseData = result['response_content']
                p.BPKErrorResponseTime = float(result['response_time_sec'])

    # TODO:
    # Create a Server Action to run set_bpk for every partner with missing bpk data or wrong bpk data and write date
    #    newer than than last BPKRequestDate or BPKErrorDate
