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


class ResPartnerBPK(models.Model):
    _name = 'res.partner.bpk'

    # FIELDS
    # res.company
    BPKRequestCompanyID = fields.Many2one(comodel_name='res.company', string="BPK Request Company",
                                          required=True, readonly=True)

    # res.partner
    BPKRequestPartnerID = fields.Many2one(comodel_name='res.partner', string="BPK Request Partner",
                                          required=True, readonly=True)

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


class ResPartnerZMRGetBPK(models.Model):
    _inherit = 'res.partner'

    # FIELDS
    BPKRequestIDS = fields.One2many(comodel_name="res.partner.bpk", inverse_name="BPKRequestPartnerID",
                                    string="BPK Requests")
    # BPK forced request values
    BPKForcedFirstname = fields.Char(string="BPK Forced Firstname")
    BPKForcedLastname = fields.Char(string="BPK Forced Lastname")
    BPKForcedBirthdate = fields.Date(string="BPK Forced Birthdate")

    # MODEL ACTIONS
    @api.model
    def request_bpk(self, firstname=str(), lastname=str(), birthdate=str()):
        responses = list()

        # Validate input
        if not all((firstname, lastname, birthdate)):
            raise ValidationError, _("Missing parameter! Mandatory are firstname, lastname and birthdate!")

        # Get the request_data_template path
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                      % soaprequest_templates
        getbpk_template = pj(soaprequest_templates, 'GetBPK_small_j2template.xml')
        assert os.path.exists(soaprequest_templates), _("GetBPK_small_j2template.xml not found at %s") \
                                                      % getbpk_template

        # Get current users company
        # TODO: Find all companies with filled pvpToken Header fields
        companies = self.env['res.company'].sudo().search([('stammzahl', '!=', False),
                                                           ('pvpToken_userId', '!=', False),
                                                           ('pvpToken_cn', '!=', False),
                                                           ('pvpToken_crt_pem', '!=', False),
                                                           ('pvpToken_prvkey_pem', '!=', False)])
        assert companies, _("No company with complete security header data found!")

        for c in companies:
            result = {'company_id': c.id,
                      'company_name': c.name,
                      'request_date': datetime.datetime.now(),
                      'request_data': "",
                      'request_url': "",
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

                # TODO: Log Request attempt
                # TODO: Create a request for each found company
                # TODO: The final return result should be a tuple with the result dicts ({}, {}, ...)
                start_time = time.time()
                response = soap_request(url="https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR",
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
                result['response_content'] = response.content
                # Todo: Log Request status (success, error and request time)

                # Process soap xml answer
                parser = etree.XMLParser(remove_blank_text=True)
                response_etree = etree.fromstring(response.content, parser=parser)
                response_pprint = etree.tostring(response_etree, pretty_print=True)

                # Response contains an error or is incomplete
                if response.status_code != 200:
                    result['response_http_error_code'] = response.status_code
                    error_code = response_etree.find(".//faultcode")
                    result['faultcode'] = error_code.text if error_code is not None else result['faultcode']
                    error_text = response_etree.find(".//faultstring")
                    result['faulttext'] = error_text.text if error_text is not None else result['faulttext']
                    # Update answer and process GetBPK for next company
                    responses.append(result)
                    continue

                # Response is valid
                private_bpk = response_etree.find(".//GetBPKReturn")
                result['private_bpk'] = private_bpk.text if private_bpk is not None else result['private_bpk']
                public_bpk = response_etree.find(".//FremdBPK")
                result['public_bpk'] = public_bpk.text if public_bpk is not None else result['public_bpk']
                # Update answer and process GetBPK for next company
                responses.append(result)

            except Exception as e:
                result['response_content'] = _("BPK Request Assertion:\n\n%s\n") % e
                responses.append(result)

        return responses

    # ACTIONS
    @api.multi
    def set_bpk(self):
        for p in self:
            # Prepare request values
            firstname = p.firstname
            lastname = p.lastname
            birthdate_web = p.birthdate_web
            if p.BPKForcedFirstname or p.BPKForcedLastname or p.BPKForcedBirthdate:
                firstname = p.BPKForcedFirstname
                lastname = p.BPKForcedLastname
                birthdate_web = p.BPKForcedBirthdate

            # Request BPK for every res.company with complete pvpToken header data
            try:
                responses = p.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate_web)
            except Exception as e:
                # If request_bpk throws an exception we log it and continue with the next partner
                logger.warning(_("BPK Request Assertion:\n\n%s\n\n") % e)
                continue

            # Create or Update the res.partner.bpk records
            for r in responses:
                values = {}
                # Process the response and transform it to a dict to create or update an res.partner.bpk record
                if not r['response_http_error_code'] and r['private_bpk'] and r['public_bpk']:
                    values = {
                        'BPKRequestCompanyID': r['company_id'],
                        'BPKRequestPartnerID': p.id,
                        'BPKPrivate': r['private_bpk'],
                        'BPKPublic': r['public_bpk'],
                        'BPKRequestDate': r['request_date'],
                        'BPKRequestData': r['request_data'],
                        'BPKRequestFirstname': firstname,
                        'BPKRequestLastname': lastname,
                        'BPKRequestBirthdate': birthdate_web,
                        'BPKResponseData': r['response_content'],
                        'BPKResponseTime': float(r['response_time_sec']),
                    }

                else:
                    values = {
                        'BPKRequestCompanyID': r['company_id'],
                        'BPKRequestPartnerID': p.id,
                        'BPKErrorCode': r['faultcode'],
                        'BPKErrorText': r['faulttext'],
                        'BPKErrorRequestDate': r['request_date'],
                        'BPKErrorRequestData': r['request_data'],
                        'BPKErrorRequestFirstname': firstname,
                        'BPKErrorRequestLastname': lastname,
                        'BPKErrorRequestBirthdate': birthdate_web,
                        'BPKErrorResponseData': r['response_content'],
                        'BPKErrorResponseTime': float(r['response_time_sec']),
                    }


                # Crete new or update existing BPK record
                bpk = self.env['res.partner.bpk'].sudo().search([('BPKRequestCompanyID.id', '=', r['company_id']),
                                                                 ('BPKRequestPartnerID.id', '=', p.id),
                                                                 ])
                assert len(bpk) <= 1, _("More than one res.partner.bpk request found for one company!")
                if bpk:
                    bpk.write(values)
                else:
                    self.env['res.partner.bpk'].sudo().create(values)


    # TODO:
    # Create a Server Action to run set_bpk for every partner with missing bpk data or wrong bpk data and write date
    #    newer than than last BPKRequestDate or BPKErrorDate
