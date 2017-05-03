# -*- coding: utf-8 -*-
import os
import errno
from os.path import join as pj
from openerp import api, models, fields
from openerp.exceptions import ValidationError, Warning
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

    # Successful BPK request
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

    # Invalid BPK request
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
    BPKForcedFirstname = fields.Char(string="BPK Forced Firstname")
    BPKForcedLastname = fields.Char(string="BPK Forced Lastname")
    BPKForcedBirthdate = fields.Date(string="BPK Forced Birthdate")

    # INTERNAL METHODS
    def _request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str()):
        responses = list()

        # Validate input
        if not (all((firstname, lastname, birthdate)) or all((firstname, lastname, zipcode))):
            raise ValidationError(_("Missing input data! Mandatory are firstname, lastname and birthdate or zip!"))

        # Get the request_data_template path
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                      % soaprequest_templates
        getbpk_template = pj(soaprequest_templates, 'GetBPK_small_j2template.xml')
        assert os.path.exists(soaprequest_templates), _("GetBPK_small_j2template.xml not found at %s") \
                                                      % getbpk_template

        # Get current users company
        # Find all companies with fully filled pvpToken Header fields
        companies = self.env['res.company'].sudo().search([('stammzahl', '!=', False),
                                                           ('pvpToken_userId', '!=', False),
                                                           ('pvpToken_cn', '!=', False),
                                                           ('pvpToken_crt_pem', '!=', False),
                                                           ('pvpToken_prvkey_pem', '!=', False),
                                                           ('BPKRequestURL', '!=', False)])
        assert companies, _("No company with complete security header data found!")

        # TODO: Assert that all companies have the same BPKRequestURL Setting (Either test or Live)

        for c in companies:
            # Check if the certificate files still exists at given path and restore them if not
            if not os.path.exists(c.pvpToken_crt_pem_path) or not os.path.exists(c.pvpToken_prvkey_pem_path):
                logger.warning(_("_request_bpk: Certificate data found but files on drive missing. "
                                 "Trying to restore files."))
                c._certs_to_file()
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

                # TODO: Log Request attempt
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
                #result['response_content'] = response.content
                # Todo: Log Request status (success, error and request time)

                # Process soap xml answer
                parser = etree.XMLParser(remove_blank_text=True)
                response_etree = etree.fromstring(response.content, parser=parser)
                response_pprint = etree.tostring(response_etree, pretty_print=True)
                result['response_content'] = response_pprint

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
                # HINT: There is a namespace attached which needs to be ignored added or removed before .find()
                # http://stackoverflow.com/questions/4440451/how-to-ignore-namespaces-with-xpath
                private_bpk = response_etree.xpath(".//*[local-name() = 'GetBPKReturn']")
                assert len(private_bpk) == 1, _("More than one GetBPKReturn node found!")
                private_bpk = private_bpk[0]
                result['private_bpk'] = private_bpk.text if private_bpk is not None else result['private_bpk']
                public_bpk = response_etree.xpath(".//*[local-name() = 'FremdBPK']/*[local-name() = 'FremdBPK']")
                assert len(public_bpk) == 1, _("More than one FremdBPK node found!")
                public_bpk = public_bpk[0]
                result['public_bpk'] = public_bpk.text if public_bpk is not None else result['public_bpk']
                # Update answer and process GetBPK for next company
                responses.append(result)

            except Exception as e:
                result['response_content'] = _("BPK Request Assertion:\n\n%s\n") % e
                responses.append(result)

        return responses

    # MODEL ACTIONS
    @api.model
    def request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str()):
        responses = list()
        assert any((birthdate, zipcode)), _("Birthdate and zipcode missing! "
                                            "You need to specify at least one them or both!")
        if birthdate:
            # 1.) Regular request BPK attempt with full birthdate
            responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate)

            # 2.) If nothing was found we try another search with birth YEAR only
            # HINT: We use all() instead of any() because the partner data should get a valid record for all companies
            #       The only exception to this rule would be if one company uses test url and the other the regular url
            #       which is an irrelevant/erroneous case.
            if len(responses) >= 1 and all(r['response_http_error_code'] for r in responses):
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
        elif zipcode and (not responses
                          or (len(responses) >= 1 and all(r['response_http_error_code'] for r in responses))):
            # 3.) If no birthdate was given or no valid response was found with the birthdate try with zipcode only
            responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate="", zipcode=zipcode)

        return responses

    # RECORD ACTIONS
    @api.multi
    def set_bpk(self):
        warning_messages = ""

        # https://www.odoo.com/es_ES/forum/ayuda-1/question/complex-many2many-domains-in-views-41777
        #('donation_deduction_optout_web', '=', False)
        #('BPKRequestIDS', '=', False) OR ('BPKRequestIDS.company_id', '')
        # TODO: write a method _bpk_update_check which returns the list of partners where a bpk request is needed
        #   - Checks donation_deduction_optout_web
        #   - Checks if a BPK request exist for every company with complete ZMR access data
        #       - If YES: Checks if the existing BPK request fields still match the values from the res.partner
        #
        # now we can compare the two record sets and only update the needed res.partner
        #
        # Maybe i should add some field to res.config and/or res.settings to set and count the absolute number of
        # request per minute and the requests per day and in the method request_bpk and throw an exception if too many

        for p in self:

            # Check for donation deduction opt out
            if p.donation_deduction_optout_web:
                warning_messages += _("Donation Deduction Opt Out is set for partner %s %s with id %s! "
                                      "BPK check skipped!\n\n") % (p.firstname, p.lastname, p.id)
                continue

            # Prepare request values
            firstname = p.firstname
            lastname = p.lastname
            birthdate_web = p.birthdate_web
            zipcode = str(p.zip) if p.zip else ""
            if p.BPKForcedFirstname or p.BPKForcedLastname or p.BPKForcedBirthdate:
                # Check for complete set of Force-BPK-Fields
                if not all((p.BPKForcedFirstname, p.BPKForcedLastname, p.BPKForcedBirthdate)):
                    warning_messages += _("Forced BPK Fields are not completely set for partner %s %s with id %s! "
                                          "BPK check skipped!\n\n") % (p.firstname, p.lastname, p.id)
                    continue
                # Overwrite BPK request data with forced settings
                firstname = p.BPKForcedFirstname
                lastname = p.BPKForcedLastname
                birthdate_web = p.BPKForcedBirthdate

            # TODO: Compare request values with existing BPK requests and companies?!?

            # Request BPK for every res.company with complete pvpToken header data
            try:
                responses = p.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate_web,
                                          zipcode=zipcode)
            except Exception as e:
                message = _("BPK-Request-Assertion for partner %s: %s %s\n%s: %s\n") % (p.id, p.firstname,
                                                                                        p.lastname,
                                                                                        e.name, e.value)
                warning_messages += message
                logger.warning(message)
                continue

            # Create or Update the res.partner.bpk records
            for r in responses:
                values = {}
                try:
                    response_time = float(r['response_time_sec'])
                except:
                    response_time = float()
                # Process the response and transform it to a dict to create or update an res.partner.bpk record
                if not r['response_http_error_code'] and r['private_bpk'] and r['public_bpk']:
                    values = {
                        'BPKRequestCompanyID': r['company_id'],
                        'BPKRequestPartnerID': p.id,
                        'BPKPrivate': r['private_bpk'],
                        'BPKPublic': r['public_bpk'],
                        'BPKRequestDate': r['request_date'],
                        'BPKRequestURL': r['request_url'],
                        'BPKRequestData': r['request_data'],
                        'BPKRequestFirstname': firstname,
                        'BPKRequestLastname': lastname,
                        'BPKRequestBirthdate': birthdate_web,
                        'BPKRequestZIP': zipcode,
                        'BPKResponseData': r['response_content'],
                        'BPKResponseTime': response_time,
                    }

                else:
                    values = {
                        'BPKRequestCompanyID': r['company_id'],
                        'BPKRequestPartnerID': p.id,
                        'BPKErrorCode': r['faultcode'],
                        'BPKErrorText': r['faulttext'],
                        'BPKErrorRequestDate': r['request_date'],
                        'BPKErrorRequestURL': r['request_url'],
                        'BPKErrorRequestData': r['request_data'],
                        'BPKErrorRequestFirstname': firstname,
                        'BPKErrorRequestLastname': lastname,
                        'BPKErrorRequestBirthdate': birthdate_web,
                        'BPKErrorRequestZIP': zipcode,
                        'BPKErrorResponseData': r['response_content'],
                        'BPKErrorResponseTime': response_time,
                    }

                # Create new or update existing BPK record
                bpk = self.env['res.partner.bpk'].sudo().search([('BPKRequestCompanyID.id', '=', r['company_id']),
                                                                 ('BPKRequestPartnerID.id', '=', p.id)])
                # Assert that only one BPK record per company exits
                if len(bpk) > 1:
                    message = _("More than one res.partner.bpk request record found "
                                "for partner %s: %s %s and company %s") % (p.id, p.firstname, p.lastname,
                                                                           r['company_id'])
                    continue
                if bpk:
                    bpk.write(values)
                else:
                    self.env['res.partner.bpk'].sudo().create(values)

        # Raise warnings exception if any
        if warning_messages:
            raise Warning(warning_messages)


    # TODO:
            # - Add set_bpk to more menu of res.partner (maybe by server action)
            # - Create a new (computed or with @api.depends) boolean field in res.partner "bpk_request_scheduled"
            #    - Always False if donation_deduction_optout_web is True
            #    - Is True if no res.partner.bpk found and valid companies
            #    - Is True if update_date of res.partner record is newer than BPKErrorRequestDate or BPKRequestDate
            #        - OR as an alternative is set to True if any of the request fields changes ? @api.depends or the "update" method


    # Server Action Example:
    # if context.get('active_model') == 'res.partner':
    #     ids = []
    #     if context.get('active_domain'):
    #         ids = self.search(cr, uid, context['active_domain'], context=context)
    #     elif context.get('active_ids'):
    #         ids = context['active_ids']
    #     self.set_bpk(cr, uid, ids, context=context)
