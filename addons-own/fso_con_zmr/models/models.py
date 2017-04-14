# -*- coding: utf-8 -*-
import os
from os.path import join as pj
from openerp import api, models, fields
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.soap import soap_request
from lxml import etree
import requests
import time
import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

class RequestError(Exception):
    pass

class CompanyAustrianZMRSettings(models.Model):
    _inherit = 'res.company'

    # Basic Settings
    stammzahl = fields.Char(string="Firmenbuch-/ Vereinsregisternummer", help='Stammzahl e.g.: XZVR-123456789')

    # PVPToken userPrincipal
    pvpToken_userId = fields.Char(string="User ID (userId)")
    pvpToken_cn = fields.Char(string="Common Name (cn)")
    pvpToken_gvOuId = fields.Char(string="Request Organisation (gvOuId)")
    pvpToken_ou = fields.Char(string="Request Person (ou)")

    # SSL Zertifikate
    crt_pem = fields.Binary(string="Certificate (PEM)", help="crt_pem")
    prvkey_pem = fields.Binary(string="Private Key (PEM)", help="prvkey_pem without password!")


class ResPartnerZMRGetBPK(models.Model):
    _inherit = 'res.partner'

    # This set of fields gets only updated if private and public bpk was returned successfully
    BPKPrivate = fields.Char(string="BPK Private", readonly=True)
    BPKPublic = fields.Char(string="BPK Public", readonly=True)
    BPKRequestDate = fields.Datetime(string="BPK Request Date")
    BPKRequestData = fields.Text(string="BPK Request Data")
    BPKResponseData = fields.Text(string="BPK Response Data")

    # This set of field gets updated by every bpk request with an error (or a missing bpk)
    BPKErrorCode = fields.Char(string="BPK-Error Code")
    BPKErrorText = fields.Text(string="BPK-Error Text")
    BPKErrorRequestDate = fields.Datetime(string="BPK-Error Request Date")
    BPKErrorRequestData = fields.Text(string="BPK-Error Request Data")
    BPKErrorResponseData = fields.Text(string="BPK-Error Response Data")

    @api.model
    def request_bpk(self, firstname=str(), lastname=str(), birthdate=str()):
        result = {'organization': "", 'request_data': "",
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
        cmp = self.env.user.company
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

        start_time = time.time()
        response = soap_request(url="https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR",
                                template=getbpk_template,
                                crt_pem=cmp.crt_pem, prvkey_pem=cmp.prvkey_pem,
                                GetBPK={
                                    "VKZ": cmp.stammzahl,
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
                                    },
                                    "BereichsKennung": "urn:publicid:gv.at:wbpk+" + cmp.stammzahl.replace('-', '+')
                                },
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
                                )
        assert response.content, _("Response has no content!")
        # TODO: Check if the response object also stores the request data (rendered jinja template data)
        # Todo: result['request_data'] = response.????
        response_time = time.time() - start_time
        result['response_time_sec'] = "%.3f" % response_time
        result['response_content'] = response.content

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

    @api.multi
    def setbpk(self):
        for partner in self:
            # TODO:
            # run request_bpk for every partner
            # update partner with the results

    # TODO:
    # Create an Action Button for setbpk
    # Create a Server Action to run setbpk for every partner with missing bpk data or wrong bpk data and write date
    #    newer than than last BPKRequestDate or BPKErrorDate
