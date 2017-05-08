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
from datetime import timedelta
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
    # TODO: Make sure Forced BPK Fields are always all filled or none (use also attr in the form view)
    BPKForcedFirstname = fields.Char(string="BPK Forced Firstname")
    BPKForcedLastname = fields.Char(string="BPK Forced Lastname")
    BPKForcedBirthdate = fields.Date(string="BPK Forced Birthdate")

    # BPK Fields for request processing and optimization
    BPKRequestInProgress = fields.Datetime(string="BPK Request in progress", readonly=True)
    BPKRequestNeeded = fields.Datetime(string="BPK Request needed", readonly=True)
    LastBPKRequest = fields.Datetime(string="Last BPK Request", readonly=True)

    # Compute BPKRequestNeeded on in 'res.partner'.write() method
    @api.multi
    def _compute_bpk_request_needed(self):
        """ If any of the depending-on fields changes set BPKRequestNeeded if all data available """
        start_time = None
        if len(self) >= 10:
            logger.info(_("Computing BPKRequestNeeded for %s partner!") % len(self))
            start_time = time.time()

        for p in self:
            if not p.donation_deduction_optout_web and (
                        all((p.firstname, p.lastname, p.birthdate_web)) or all((p.firstname, p.lastname, p.zip))):
                if not p.BPKRequestNeeded:
                    logger.warning("TESTING ONLY: Set BPKRequestNeeded for %s" % p.name)
                    p.BPKRequestNeeded = fields.datetime.now()
                continue
            # Data is missing or donation_deduction_optout_web set
            if p.BPKRequestNeeded:
                logger.warning("TESTING ONLY: Unset BPKRequestNeeded for %s" % p.name)
                p.BPKRequestNeeded = None

        if start_time:
            processing_time = time.time() - start_time
            logger.info(_("Computed BPKRequestNeeded for %s in %.3f") % (len(self), processing_time))

    # Compute BPKRequestNeeded
    @api.multi
    def write(self, vals):
        """Override write to check for BPKRequestNeeded"""
        # Write to partners
        # HINT: Returns only True or False!
        result = super(ResPartnerZMRGetBPK, self).write(vals)
        # Check if any relevant field for BPKRequestNeeded is in vals
        if result and any(key in vals for key in ['firstname', 'lastname', 'birthdate_web', 'zip']):
            self._compute_bpk_request_needed()
        return result

    # INTERNAL METHODS
    def _find_bpk_companies(self):
        """
        :return: res.company recordset
        """
        # Find all companies with fully filled pvpToken Header fields
        companies = self.env['res.company'].sudo().search([('stammzahl', '!=', False),
                                                           ('pvpToken_userId', '!=', False),
                                                           ('pvpToken_cn', '!=', False),
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
        assert any((birthdate, zipcode)), _("Birthdate and zipcode missing! "
                                            "You need to specify at least one them or both!")

        # Process Lastname
        lastnames_to_check = [lastname]
        split_lastname = lastname.split('-')[0] if '-' in lastname else lastname.split(' ')[0] if ' ' in lastname \
            else ''
        if split_lastname:
            lastnames_to_check.append(split_lastname)

        # Start BPK Request(s)
        responses = list()
        for lastname in lastnames_to_check:
            if birthdate:
                # BPK Request attempt with full birthdate
                responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate)
                if self.response_ok(responses):
                    return responses

                # BPK Request attempt with birth YEAR only
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
                    if self.response_ok(responses):
                        return responses

            if zipcode:
                # BPK Request attempt with zipcode only
                responses = self._request_bpk(firstname=firstname, lastname=lastname, birthdate="", zipcode=zipcode)
                if self.response_ok(responses):
                    return responses

        # BPK not found
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
        partners = self
        warning_messages = ""

        # Check partners for donation donation_deduction_optout_web
        ddow = self.env['res.partner'].search([('id', 'in', self.ids),
                                               ('donation_deduction_optout_web', '!=', False)])
        if ddow:
            warning_messages += _("Donation Deduction Opt Out is set for partners:\n%s\n "
                                  "BPK check skipped for them!\n\n") % ddow.ids
            partners = partners - ddow

        # Check partners if they are already in processing
        # ATTENTION: Ignore the BPKRequestInProgress field if older than 'request_in_progress_limit' days to recover
        #            from terminated processes or exceptions.
        # TODO: set timedelate days value from res.config setting
        brip = self.env['res.partner'].search(
            [('id', 'in', self.ids),
             ('BPKRequestInProgress', '!=', False),
             ('BPKRequestInProgress', '>', str(fields.datetime.now() - timedelta(days=1)))
             ])
        if brip:
            warning_messages += _("BPK request in progress for partners:\n%s\n "
                                  "BPK check skipped for them!\n\n") % brip.ids
            partners = partners - brip

        # Mark all remaining partners with 'BPK Request In Progress' to avoid double calls of different workers
        partners.write({'BPKRequestInProgress': fields.datetime.now()})

        # Process BPK Requests
        for p in partners:
            # Prepare request values
            firstname = p.firstname
            lastname = p.lastname
            birthdate_web = p.birthdate_web
            zipcode = str(p.zip) if p.zip else ""
            if p.BPKForcedFirstname or p.BPKForcedLastname or p.BPKForcedBirthdate:
                # Check for complete set of Force-BPK-Fields
                if not all((p.BPKForcedFirstname, p.BPKForcedLastname, p.BPKForcedBirthdate)):
                    message = _("Forced BPK Fields are not completely set for partner %s %s with id %s! "
                                "BPK check skipped!\n\n") % (p.firstname, p.lastname, p.id)
                    warning_messages += message
                    logger.error(message)
                    continue
                # Overwrite BPK request data with forced settings
                firstname = p.BPKForcedFirstname
                lastname = p.BPKForcedLastname
                birthdate_web = p.BPKForcedBirthdate

            # Request BPK for every res.company with complete pvpToken header data
            try:
                responses = p.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate_web,
                                          zipcode=zipcode)
            except Exception as e:
                message = _("BPK-Request-Assertion for partner %s: %s %s\n%s\n") % (p.id, p.firstname, p.lastname, e)
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
                    warning_messages += message
                    logger.error(message)
                    continue
                if bpk:
                    bpk.write(values)
                else:
                    self.env['res.partner.bpk'].sudo().create(values)

            # Mark partner as DONE for BPK
            # HINT: We add two seconds of safety to LastBPKRequest Date to avoid conflicts with write_date in domains
            p.write({'BPKRequestInProgress': None,
                     'BPKRequestNeeded': None,
                     'LastBPKRequest': fields.datetime.now() + timedelta(seconds=2)})

        # Raise warning exception if any warning_messages exits
        if warning_messages:
            raise Warning(warning_messages)

    # (MODEL) ACTIONS FOR AUTOMATED BPK PROCESSING
    @api.model
    def find_bpk_partners_to_update(self, full_search=False, skip_no_bpk=False,
                                    limit=1, order='write_date DESC', batch=10000):
        """
        # HINT: LIFO: As an optimization we reverse the order to latest first because it is very likely that we want the 
        #       latest updated records to be processed first and also that these records would most likely have relevant
        #       changes. In the circumstance that there is not enough time to process all bpk records the oldest ones
        #       would never be processed but this is just as bad or even worse as that youngest ones will never be
        #       processed.
        #
        :param full_search: bool # If True ignore BPKRequestNeeded and do a full search
        :param limit: int # maximum quantity of partners to process, use 0 or None for no limit!
        :param order: char # field to sort by and sort order (DESC or ASC) e.g.: 'write_date ASC' 
                             ASC=regular DESC=reverse for .sorted() record set operation
                             ASC on date fields means oldest first (Ascend from oldest date to newest date)
                             DESC on date fields means newest first (Descend from newest date to oldest date)
        :param skip_no_bpk: bool # Do not check for res.partner without bpk requests
        :param batch: int # Batch size for the processing of partners with bpk records.
                            This is useful for memory / speed optimization
        :return: recordset # res.partner
        """
        # TODO: BPKRequestInProgress should be honored in Regular and Full search - maybe days selectable by option and
        #       not honored if option is 0 or none like limit
        # --------------
        # REGULAR SEARCH
        # --------------
        if not full_search:
            domain = [('BPKRequestNeeded', '!=', False)]
            if skip_no_bpk:
                domain.append(('BPKRequestIDS', '!=', False))
            partners_to_update = self.env['res.partner'].search(domain, limit=limit, order=order)
            return partners_to_update

        # -----------
        # FULL SEARCH
        # -----------
        # Create an empty record set
        partners_to_update = self.env['res.partner']

        # Find all companies with fully filled ZMR access fields
        try:
            companies = self._find_bpk_companies()
        except Exception as e:
            logger.error(_("_find_bpk_partners: Exception while fetching companies:\n%s\n") % e)
            return partners_to_update

        # 1.) Find res.partner without res.partner.bpk
        if skip_no_bpk:
            partner_without_bpks = partners_to_update
        else:
            partner_without_bpks = self.env['res.partner'].search([
                ('donation_deduction_optout_web', '=', False),
                ('BPKRequestIDS', '=', False),
                ('firstname', '!=', False),
                ('lastname', '!=', False),
                '|',
                    ('birthdate_web', '!=', False),
                    ('zip', '!=', False)], order=order, limit=limit)
            # Return if we have already enough partners found
            if limit and len(partner_without_bpks) >= limit:
                return partner_without_bpks
            else:
                partners_to_update = partners_to_update | partner_without_bpks

        # 2.) Find res.partner(s) to update with existing res.partner.bpk(s)
        # HINT: Must use all partners without limit for further checks!
        # HINT: To load 1.000.000 res.partner from database to memory takes approximately 30 seconds
        # HINT: remaining -1 means No Limit = Find all partners with bpks to update
        offset = 0
        remaining = -1 if not limit else limit - len(partner_without_bpks)
        while remaining:
            # TODO: A good optimization would be to check if write_date is older than LastBPKRequest
            #       with a direct database select instead of a domain search - should ask sebi or try it my self :)
            # http://stackoverflow.com/questions/27346751/openerp-domain-filters-how-to-compare-2-fields-in-object
            partner_with_bpks = self.env['res.partner'].search([
                ('donation_deduction_optout_web', '=', False),
                ('BPKRequestIDS', '!=', False),
                ('firstname', '!=', False),
                ('lastname', '!=', False),
                '|',
                    ('birthdate_web', '!=', False),
                    ('zip', '!=', False)], order=order, limit=batch, offset=offset)
            offset = offset + batch

            for p in partner_with_bpks:
                # Stop if enough partners are found
                if remaining == 0:
                    break

                # 2.1.) Check if there are missing or too many BPK request
                bpk_company_ids = [r.BPKRequestCompanyID.id for r in p.BPKRequestIDS]
                # Check if bpk_company_ids contains ids not in current companies
                # HINT: s - t = new set with elements in s but not in t
                orphan_records = set(bpk_company_ids) - set(companies.ids)
                if orphan_records:
                    logger.error(_("BPK Records %s found for non existing companies "
                                   "or companies where the ZMR BPK access data was removed "
                                   "for partner %s: %s %s") % (orphan_records, p.id, p.firstname, p.lastname))
                # Check if any bpk records are missing for current companies
                # HINT: s - t = new set with elements in s but not in t
                if set(companies.ids) - set(bpk_company_ids):
                    partners_to_update = partners_to_update | p
                    remaining = remaining - 1
                    continue

                # 2.2.) Check if in any BPK request the bpk request data neither for regular nor for error request
                #       matches the current partner request data and therefore was changed and must be requested again.
                for r in p.BPKRequestIDS:
                    if r.BPKRequestCompanyID.id in companies.ids and (
                        not ((p.firstname == r.BPKRequestFirstname and
                             p.lastname == r.BPKRequestLastname and
                             p.birthdate_web == r.BPKRequestBirthdate and
                             p.zip == r.BPKRequestZIP)
                            or
                            (p.firstname == r.BPKErrorRequestFirstname and
                             p.lastname == r.BPKErrorRequestLastname and
                             p.birthdate_web == r.BPKErrorRequestBirthdate and
                             p.zip == r.BPKErrorRequestZIP)
                           )):
                        partners_to_update = partners_to_update | p
                        remaining = remaining - 1
                        break

            # Stop while loop if all partners are processed
            remaining = None

        # Sort partners_to_update
        sort_field = order.split(' ', 1)[0]
        reverse = False if order.endswith('ASC') else True
        partners_to_update = partners_to_update.sorted(key=lambda l: getattr(l, sort_field), reverse=reverse)

        # Return the res.partner recordset
        return partners_to_update

    @api.multi
    def tester(self):
        start_time = time.time()
        logger.warning("START FULL find_bpk_partners_to_update but with no limit and skip_no_bpk=True")
        partners = self.find_bpk_partners_to_update(full_search=True, limit=0, skip_no_bpk=False)
        end_time = start_time - time.time()
        logger.warning("END FULL find_bpk_partners_to_update in %.3f: %s partners found" % (end_time, len(partners)))

    # TODO: Create a scheduled server action which runs regular bpk updates
    #       Should run every hour and therefore set_bpk_automated(self, limit=800, timeout=3540)
    #       which means a maximum request amount of 800*24 = 19200 in 24 hours leaving enough space for non stored
    #       gui requests from FS and FSO

    # TODO: Create a server actions which "checks" all res.partner for BPKRequestNeeded and scedule this action
    #       every week. Make sure the method find_bpk_partners_to_update with full search also finds records with
    #       BPKRequestInProgress older than .. value!

    # Server Action Example:
    # if context.get('active_model') == 'res.partner':
    #     ids = []
    #     if context.get('active_domain'):
    #         ids = self.search(cr, uid, context['active_domain'], context=context)
    #     elif context.get('active_ids'):
    #         ids = context['active_ids']
    #     self.set_bpk(cr, uid, ids, context=context)
