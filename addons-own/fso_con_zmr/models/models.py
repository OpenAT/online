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
    # TODO: Make sure forced BPK fields are always all filled or none (now only done by attr in the form view)
    BPKForcedFirstname = fields.Char(string="BPK Forced Firstname")
    BPKForcedLastname = fields.Char(string="BPK Forced Lastname")
    BPKForcedBirthdate = fields.Date(string="BPK Forced Birthdate")
    BPKForcedZip = fields.Char(string="BPK Forced ZIP")

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
    BPKRequestError = fields.Text(string="BPK Request Exception", readonly=True)

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

    # Methods to store BPK field names
    def _bpk_regular_fields(self):
        return ['firstname', 'lastname', 'birthdate_web']

    def _bpk_optional_regular_fields(self):
        return ['zip']

    def _bpk_forced_fields(self):
        return ['BPKForcedFirstname', 'BPKForcedLastname', 'BPKForcedBirthdate']

    def _bpk_optional_forced_fields(self):
        return ['BPKForcedZip']

    def _bpk_fields(self):
        return self._bpk_regular_fields() + self._bpk_optional_regular_fields() + \
               self._bpk_forced_fields() + self._bpk_optional_forced_fields()

    # ----------------------
    # EXTEND DEFAULT METHODS
    # ----------------------
    @api.model
    def create(self, values, no_bpkrequestneeded_check=False):
        # BPK forced fields integrity check
        if any(values.get(field, False) for field in self._bpk_forced_fields()):
            assert all(values.get(field, False) for field in self._bpk_forced_fields()), \
                _("All required BPK Forced Fields must be set! Required are: %s" % self._bpk_forced_fields())

        # Check if donation_deduction_optout_web is set
        if values.get('donation_deduction_optout_web', False):
            values['BPKRequestNeeded'] = False
            return super(ResPartnerZMRGetBPK, self).create(values)

        # No Checks if BPKRequestNeeded is set manually or create was called with no_bpkrequestneeded_check set
        # ATTENTION: sosync v1 and v2 will NOT sync the field BPKRequestNeeded. The may use no_bpkrequestneeded_check
        #            to suppress immediate bpk request checks after partner creation or update.
        #            This may only be useful after BPK file imports in FS.
        if values.get('BPKRequestNeeded', False) or no_bpkrequestneeded_check:
            return super(ResPartnerZMRGetBPK, self).create(values)

        # Check if BPKRequestNeeded must be set
        if all(values.get(field, False) for field in self._bpk_forced_fields()):
            values['BPKRequestNeeded'] = fields.datetime.now()
        elif all(values.get(field, False) for field in self._bpk_regular_fields()):
            values['BPKRequestNeeded'] = fields.datetime.now()

        # Return
        return super(ResPartnerZMRGetBPK, self).create(values)

    @api.multi
    def write(self, vals):
        """Override write to check for BPKRequestNeeded"""

        # No Checks if Donation Deduction Opt Out is going to be set to True
        # HINT: Manually set BPKRequestNeeded does not matter if donation_deduction_optout_web is set to True
        if vals.get('donation_deduction_optout_web', False):
            vals['BPKRequestNeeded'] = None
            return super(ResPartnerZMRGetBPK, self).write(vals)

        # No Checks if BPKRequestNeeded is set manually or create was called with no_bpkrequestneeded_check set
        # ATTENTION: sosync v1 and v2 will !NOT! sync the field BPKRequestNeeded. The may use no_bpkrequestneeded_check
        #            to suppress immediate bpk request checks after partner creation or update.
        #            This may only be useful after BPK file imports in FS.
        if 'BPKRequestNeeded' in vals:
            return super(ResPartnerZMRGetBPK, self).write(vals)

        # Compute BPKRequestNeeded
        # ------------------------
        # HINT: Even if there is already a BPK-Request we can assume that if data changed the bpkrequest needs to be
        #       done again. This may not be 100% exact but is fast and easy and false positives are no problem anyway!
        # ATTENTION: Since sosync v1 always sends all fields, even if they are empty or unchanged,
        #            we need to really compare the values of the fields.

        # Check if there are any BPK relevant field in vals
        fields_to_check = [field for field in self._bpk_fields() if field in vals]
        partners_bpk_needed = []
        if fields_to_check:
            partners_bpk_needed = self.env['res.partner']
            for p in self:
                optional_fields = self._bpk_optional_forced_fields() + self._bpk_optional_regular_fields()

                # 1.) Skip any further testing if donation_deduction_optout_web is set for this partner
                if p.donation_deduction_optout_web:
                    if p.BPKRequestNeeded:
                        p.BPKRequestNeeded = None
                    continue

                # 2.) Check forced BPK fields for changes
                if any(field for field in self._bpk_forced_fields() if field in vals):

                    # Check forced field integrity
                    # HINT: This test will only run if at least one of the forced fields is set in vals (see 'if' above)
                    #       Therefore if one field is set all fields must be set either in vals or they must have had
                    #       a value before already.
                    assert all(vals.get(field) if field in vals else p[field] for field in self._bpk_forced_fields()), \
                        _("All required BPK Forced Fields must be set! Required are: %s" % self._bpk_forced_fields())

                    # Check for any changes to the mandatory forced fields
                    # HINT: This test will only run if at least one of the forced fields is set in vals (see 'if' above)
                    #       Therefore 'if field in vals' is enough: We do not need to check here if the field has
                    #       a value or is set to False
                    if any(vals[field] != p[field] for field in self._bpk_forced_fields() if field in vals):
                        partners_bpk_needed = partners_bpk_needed | p
                    continue

                # 3.) Check regular BPK fields for changes
                elif any(field for field in self._bpk_regular_fields() if field in vals):
                    # Make sure all regular fields are set that are required for a bpk request
                    if all(vals.get(field) if field in vals else p[field] for field in self._bpk_regular_fields()):
                        # Check if data has changed
                        if any(vals[field] != p[field] for field in self._bpk_regular_fields() if field in vals):
                            partners_bpk_needed = partners_bpk_needed | p
                        continue

                # 4.) Check optional BPK fields for changes
                elif any(field for field in optional_fields if field in vals):

                    # Only check optional BPK field changes if no valid bpk request exits
                    if not p.BPKRequestIDS or (p.BPKRequestIDS and not p.BPKRequestIDS[0].BPKPrivate):

                        # Check optional forced fields
                        if all(vals.get(field) if field in vals else p[field] for field in self._bpk_forced_fields()):
                            if any(vals[f] != p[f] for f in self._bpk_optional_forced_fields() if f in vals):
                                partners_bpk_needed = partners_bpk_needed | p
                            continue

                        # Check optional regular fields
                        elif all(vals.get(f) if f in vals else p[f] for f in self._bpk_regular_fields()):
                            if any(vals[f] != p[f] for f in self._bpk_optional_regular_fields() if f in vals):
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

        # Return
        # ------
        return super(ResPartnerZMRGetBPK, self).write(vals)

    # ----------------
    # INTERNAL METHODS
    # ----------------
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

        # Assert there is at least one company with valid ZMR data
        assert companies, _("No company found with complete Austrian ZMR access data!")

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

    # Try __request_bpk() multible times based on errors
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

    # Simple response status checker (may be used by java script or by FS)
    def response_ok(self, responses):
        if len(responses) >= 1 and not any(r['faulttext'] for r in responses):
            return True
        else:
            return False

    # Check if the request data matches the partner data
    @api.multi
    def bpk_requests_matches_partner_data(self):
        assert self.ensure_one(), _("bpk_requests_matches_partner_data() is only allowed for one partner at once")
        p = self[0]

        # Get valid bpk companies
        bpk_companies = self._find_bpk_companies()

        # Data is not matching if no BPK Requests to check is available
        if not self.BPKRequestIDS or not [r for r in p.BPKRequestIDS if r.BPKRequestCompanyID.id in bpk_companies.ids]:
            return False

        # Prepare the partner data to compare
        if any(p[field] for field in self._bpk_forced_fields()):
            partner_data = {'firstname': p.BPKForcedFirstname or '',
                            'lastname': p.BPKForcedLastname or '',
                            'birthdate': p.BPKForcedBirthdate or '',
                            'zipcode': p.BPKForcedZip or '',
                            }
        else:
            partner_data = {'firstname': p.firstname or '',
                            'lastname': p.lastname or '',
                            'birthdate': p.birthdate_web or '',
                            'zipcode': p.zip or '',
                            }

        # CHECK IF THE DATA OF ALL BPK-REQUESTS MATCH THE DATA OF THE PARTNER FIELDS
        # HINT: If any of the BPK Request data does not match the current partner data we return 'False'
        # ATTENTION: False == u'' will resolve to False! Therefore we use " ... or '' "
        for r in p.BPKRequestIDS:
            # ATTENTION: Only check non orphan bpk records so we do not reinclude them again and again
            if r.BPKRequestCompanyID.id in bpk_companies.ids:

                # Prepare the bpk request data to compare
                if r.BPKErrorRequestDate > r.BPKRequestData:
                    bpk_data = {'firstname': r.BPKErrorRequestFirstname or '',
                                'lastname': r.BPKErrorRequestLastname or '',
                                'birthdate': r.BPKErrorRequestBirthdate or '',
                                'zipcode': r.BPKErrorRequestZIP or '',
                                }
                else:
                    bpk_data = {'firstname': r.BPKRequestFirstname or '',
                                'lastname': r.BPKRequestLastname or '',
                                'birthdate': r.BPKRequestBirthdate or '',
                                'zipcode': r.BPKRequestZIP or '',
                                }

                # Compare the data
                if any(partner_data[field] != bpk_data[field] for field in partner_data):
                    # If unequal data was found return false
                    return False

        # Data matches!
        return True

    # -------------
    # MODEL ACTIONS
    # -------------
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
    def set_bpk_request_needed(self):
        logger.info("set_bpk_request_needed() for ids %s" % self.ids)
        return self.write({'BPKRequestNeeded': fields.datetime.now()})

    @api.multi
    def remove_bpk_request_needed(self):
        logger.info("remove_bpk_request_needed() for ids %s" % self.ids)
        return self.write({'BPKRequestNeeded': False})

    @api.multi
    def set_bpk(self):
        """
        Creates or Updates BPK request for the given partner recordset (=BPKRequestIDS)

        HINT: Runs request_bpk() for every partner.
              Exception text will be written to BPKRequestError if request_bpk() raises one

        ATTENTION: Will also update partner fields: BPKRequestNeeded, LastBPKRequest, BPKRequestError and
                   BPKRequestInProgress

        :return: dict, partner id and related error if any was found
        """
        # TODO: Set BPKRequestInProgress ?

        # MAKE SURE THERE IST AT LEAST ONE COMPANY WITH FULL ZMR ACCESS DATA
        # ATTENTION: request_bpk() would throw an exception if no company was found and this exception would then
        #            be written to every partner. This is not what we want if there is no company found therefore
        #            we just stop here before we update the partner or their BPK request(s)
        companies = self._find_bpk_companies()

        # HELPER METHOD: FINAL PARTNER UPDATE
        def finish_partner(partner, bpk_request_error=None, last_bpk_request=fields.datetime.now()):
            vals = {'BPKRequestNeeded': None,
                    'BPKRequestInProgress': None,
                    'LastBPKRequest': last_bpk_request,
                    'BPKRequestError': bpk_request_error}
            return partner.write(vals)

        # GLOBAL ERROR DICTIONARY
        # Format: {partner_id: "Error or exception text", ...}
        errors = dict()

        # BPK REQUEST FOR EACH PARTNER
        # ----------------------------
        start_time = time.time()

        for p in self:
            faulttext = None

            # Stop if the partner data matches the bpk requests data
            # TODO: If at one point we MUST force the request because of ZMR changes we would need to add an option
            #       in the interface: e.g.: 'force_request'. But be careful: if there are options in the interface
            #       set_bpk() could not be called by buttons or server actions directly any more because of
            #       mapping problems from old api to new api (just create a wrapper method like for the buttons)
            if p.bpk_requests_matches_partner_data():
                errors[p.id] = _("%s (ID %s): Skipped BPK request! Partner data matches existing BPK request data!") \
                               % (p.name, p.id)
                if not p.LastBPKRequest:
                    finish_partner(p, bpk_request_error=errors[p.id])
                else:
                    finish_partner(p, bpk_request_error=errors[p.id], last_bpk_request=p.LastBPKRequest)
                # Continue with next partner
                continue

            # Stop if donation_deduction_optout_web is set
            if p.donation_deduction_optout_web:
                errors[p.id] = _("%s (ID %s): Donation Deduction Opt Out is set!") % (p.name, p.id)
                finish_partner(p, bpk_request_error=errors[p.id])
                continue

            # Prepare BPK request values
            if any(p[forced_field] for forced_field in self._bpk_forced_fields()):
                firstname = p.BPKForcedFirstname
                lastname = p.BPKForcedLastname
                birthdate_web = p.BPKForcedBirthdate
                zipcode = p.BPKForcedZip
            else:
                firstname, lastname, birthdate_web, zipcode = p.firstname, p.lastname, p.birthdate_web, p.zip

            # Run request_bpk()
            try:
                start_time = time.time()
                # HINT: request_bpk will() clean the names and try the ZMR request multiple times if needed
                resp = self.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate_web,
                                        zipcode=zipcode)
                assert resp, _("%s (ID %s): No BPK-Request response(s)!")
            except Exception as e:
                errors[p.id] = _("%s (ID %s): BPK-Request exception: %s") % (p.name, p.id, e)
                finish_partner(p, bpk_request_error=errors[p.id])
                continue

            # Create or update BPK requests from responses
            for r in resp:
                faulttext = None

                # 4.1) Prepare values for the bpk_request record
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

                # Search for an existing bpk record
                # HINT: This search order will list BPK records with a BPK key found by newest write date!
                #       So the first entry is the one we want to keep in case there is more than one found per company
                bpk = self.env['res.partner.bpk'].sudo().search(
                    [('BPKRequestCompanyID.id', '=', r['company_id']), ('BPKRequestPartnerID.id', '=', p.id)],
                    order="BPKPrivate DESC, BPKPublic DESC, write_date DESC"
                )

                # Make sure only one bpk records exist per company for this partner
                # ATTENTION: Delete all but one res.partner.bpk record if there is more than one record per company
                # HINT: Only one bpk record per partner per company is allowed. If there is more than one we can
                #       be sure this is an error. It was most likely an concurrent request update after a sync from FS
                if len(bpk) > 1:
                    try:
                        # MORE THAN ONE RECORD FOUND FOR THIS COMPANY:
                        # Delete all bpk records but the newest one with a set bpk key
                        bpk_to_keep = bpk[0]
                        bpk_to_delete = bpk[1:]
                        bpk_to_delete.unlink()

                        # Set the bpk-record-to-update to the kept BPK record
                        bpk = bpk_to_keep

                    except Exception as e:
                        # BPK RECORD DELETION FAILED:
                        errors[p.id] = _("%s (ID %s): More than one BPK record per company found "
                                         "and removal of BPK records failed also: %s") % (p.name, p.id, e)
                        # Update the partner and stop processing other responses but continue with the next partner
                        finish_partner(p, bpk_request_error=errors[p.id])
                        break

                # Create a new bpk record or update the exiting one
                if bpk:
                    bpk.write(values)
                else:
                    # HINT: This would also update the partner Many2one BPK record field
                    self.env['res.partner.bpk'].sudo().create(values)

                # END: Response processing for loop

            # Finally update the partner after all responses created or updated its bpk requests
            # HINT: We use 'faulttext' only from the last bpk request for this partner but
            #       this should be no problem since all 'faulttext' must be identical
            finish_partner(p, bpk_request_error=faulttext)

            # END: partner for loop

        # Log runtime and error dictionary
        logger.info("set_bpk(): Processed %s partners in %.3f seconds" % (len(self), time.time()-start_time))
        if errors:
            logger.warning("set_bpk(): Partners with errors: \n%s\n\n" % pp.pprint(errors))

        # RETURN ERROR DICTIONARY
        # HINT: An empty dict() means no errors where found!
        return errors

    # --------------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED BPK PROCESSING
    # --------------------------------------------
    @api.multi
    def find_bpk_partners_to_update(self,
                                    quick_search=True,
                                    search_all_partner=False,
                                    limit=1,
                                    order='BPKRequestNeeded DESC, write_date DESC',
                                    skip_partner_with_bpk_records=False,
                                    fs_in_progress_range=48,
                                    fs_batch_size=10000):
        """
        # HINT: LIFO: As an optimization we reverse the order to latest first because it is very likely that we want the 
        #       latest updated records to be processed first and also that these records would most likely have relevant
        #       changes. In the circumstance that there is not enough time to process all bpk records the oldest ones
        #       would never be processed but this is just as bad or even worse as that youngest ones will never be
        #       processed.
        # ATTENTION: fs_... are options for the full search. In other words: would only have an effect if quick_search
        #            is set to False
        #
        :return: res.partner recordset
        """
        # Start with an empty record set
        partners_to_update = self.env['res.partner']
        domain = []
        # Search only for records in self if search_all_partner is False
        if not search_all_partner:
            if not self.ids:
                return partners_to_update
            domain += [('id', 'in', self.ids)]

        # ============
        # QUICK SEARCH
        # ============
        # Used by the method scheduled_set_bpk() which is normally started every minute by a scheduled
        # server action created by xml
        #
        # HINT: "donation_deduction_optout_web" and "BPKRequestInProgress" are checked by set_bpk() so we do not
        #       need to check it here also. If there are already false positives they will be clean after set_bpk()
        if quick_search:

            # Search only for partner where BPKRequestNeeded is set
            domain += [('BPKRequestNeeded', '!=', False)]

            # Search only for partner without bpk records
            # HINT: This may be useful if you want to process partners with no existing bpk records first
            if skip_partner_with_bpk_records:
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

        # Find all companies with fully filled ZMR access fields
        try:
            bpk_companies = self._find_bpk_companies()
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
        domain += [
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
              ('BPKRequestInProgress', '<', str(fields.datetime.now() - timedelta(hours=fs_in_progress_range))),
              ('BPKRequestInProgress', '>', str(fields.datetime.now() + timedelta(hours=fs_in_progress_range)))
            ]

        # A.) FIND PARTNERS TO UPDATE WITH NO BPK RECORDS
        # -----------------------------------------------
        logger.info("find_bpk_partners_to_update(): A.) FIND PARTNERS-TO-UPDATE WITH NO BPK RECORDS FIRST")

        # Create search domain for partners with no existing BPK records
        domain_without_bpk = domain + [('BPKRequestIDS', '=', False)]
        logger.info("Search domain for partners with no BPK records:\n%s\n" % domain_without_bpk)

        # Search for partners with no existing BPK records
        partner_without_bpks = self.env['res.partner'].search(domain_without_bpk, order=order, limit=limit)
        logger.info("Found %s partners without existing BPK records." % len(partner_without_bpks))

        # STOP AND RETURN: if limit is reached or skip_partner_with_bpk_records is set
        if skip_partner_with_bpk_records or (limit and len(partner_without_bpks) >= limit):
            return partner_without_bpks

        # B.) FIND PARTNERS TO UPDATE WITH EXISTING BPK RECORDS
        # -----------------------------------------------------
        # - Find only partners that fulfill the minimum requirements for a bpk check (see base_domain)
        # - Check if latest bpk request data and current partner data are different
        # HINT: If skip_partner_with_bpk_records is set this would be never reached! (Look above: Stopped at point A.)
        # ATTENTION: At some point this search will check !!! ALL !!! partners with BPK records
        #            so make sure to run the full search not too often!
        logger.info("find_bpk_partners_to_update(): B.) FIND PARTNERS-TO-UPDATE WITH EXISTING BPK RECORDS")

        # Use partner_without_bpks as the starting point (may be an empty recordset)
        partners_to_update = partner_without_bpks

        # Create search domain for partners with existing BPK records
        domain_with_bpk = domain + [('BPKRequestIDS', '!=', False)]
        logger.info("Search domain for partners with BPK records:\n%s\n" % domain_with_bpk)

        # CHECK PARTNERS
        # ATTENTION: To load one million res.partner from database to memory takes approximately 30 seconds
        #            Therefore we use batches of fs_batch_size=10000 to optimize read time and memory
        # HINT: remaining -1 = no limit (Check all partners with bpk records)
        offset = 0
        remaining = -1 if not limit else limit - len(partner_without_bpks)
        while remaining:

            # Find partner batch
            partner_with_bpks = self.env['res.partner'].search(domain_with_bpk,
                                                               order=order, limit=fs_batch_size, offset=offset)

            # Stop while loop if no partner where found
            if not partner_with_bpks:
                logger.info("No partners with existing bpk records left to check !")
                break

            # Log info
            logger.info("Start batch of %s parnter to check if a BPK request is needed" % len(partner_with_bpks))

            # CHECK THE PARTNER
            for p in partner_with_bpks:

                # EXIT PARTNER LOOP: Stop to check partner if remaining (=limit) is reached
                # HINT: Will never stop here if remaining started negative e.g. with -1
                if remaining == 0:
                    break

                # Get the company ids (recordset) for all BPK requests linked to this partner
                partner_bpkrequests_company_ids = [r.BPKRequestCompanyID.id for r in p.BPKRequestIDS]

                # A) CHECK FOR MISSING BPK RECORDS FOR VALID COMPANIES
                #    (e.g.: on new company creation or zmr access data was set for existing companies)
                # HINT: s - t = new set with elements in s but not in t
                if set(bpk_companies.ids) - set(partner_bpkrequests_company_ids):
                    partners_to_update = partners_to_update | p
                    remaining = remaining - 1
                    continue

                # B) CHECK FOR BPK REQUESTS LINKED TO INVALID COMPANIES (ORPHAN RECORDS)
                #    (Deleted company or deleted zmr access data)
                #
                # ATTENTION: We will not delete the BPK records but just log an error!
                #            Also they will not be deleted by set_bpk()!
                #            This is a safety net if someone ACCIDENTALLY deleted access data of a company
                #
                # HINT: s - t = new set with elements in s but not in t
                orphan_bpk_records = set(partner_bpkrequests_company_ids) - set(bpk_companies.ids)
                if orphan_bpk_records:
                    logger.error(_("BPK Records %s found for non existing companies "
                                   "or companies where the ZMR BPK access data was removed "
                                   "for partner %s: %s %s") % (orphan_bpk_records, p.id, p.firstname, p.lastname))

                # C) CHECK FOR MORE THAN ONE BPK RECORD PER VALID COMPANY
                #    (may only be caused by sosync errors or concurrent updates)
                #
                # ATTENTION: set_bpk() will clean the unnecessary bpk records!
                #
                # HINT: If a bpk record exists for this partner and the same res.company it is an error.
                #       partner_bpkrequests_company_ids would look something like this [1, 1, 2]
                # HINT: Remove any orphan records from the list or this partner would always be added again
                valid_bpk_company_ids = [i for i in partner_bpkrequests_company_ids if i not in orphan_bpk_records]
                if len(valid_bpk_company_ids) != len(set(valid_bpk_company_ids)):
                    logger.error("More than one BPK Record found for the same company for partner %s (ID: %s)" %
                                 (p.name, p.id))
                    partners_to_update = partners_to_update | p
                    remaining = remaining - 1
                    continue

                # D) CHECK IF THE DATA OF ALL BPK-REQUESTS MATCH THE DATA OF THE PARTNER FIELDS
                #    HINT: Forced BPK fields takes precedence
                #    ATTENTION: False == u'' will resolve to False! Therefore we use " ... or '' "
                if not p.bpk_requests_matches_partner_data():
                    partners_to_update = partners_to_update | p
                    remaining = remaining - 1
                    continue

                # END: PARTNER FOR LOOP

            # PROCEED WITH WHILE LOOP: START NEXT BATCH OF PARTNERS
            # Create offset for next batch of partners to process
            offset += fs_batch_size

        # SORT THE RECORD SET
        sort_field = order.split(' ', 1)[0]
        reverse = False if order.endswith('ASC') else True
        partners_to_update = partners_to_update.sorted(key=lambda l: getattr(l, sort_field), reverse=reverse)

        # RETURN THE RECORD SET
        logger.info(_("Full search: Total partners found requiring a BPK request: %s") % len(partners_to_update))
        return partners_to_update

    @api.model
    def scheduled_set_bpk(self, max_requests_per_minute=120):
        start_time = time.time()
        logger.info(_("scheduled_set_bpk() START"))

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
            max_runtime_in_seconds = int(scheduled_action.interval_number *
                                         interval_to_seconds[scheduled_action.interval_type])

            # Set the limit of partners to request BPKs based on interval and max_requests_per_minute
            # HINT: set_bpk may run up to four times per BPK request try BUT it is a save bet to assume
            #       that most of the time one request is enough.
            #       However: Try to set the max_requests_per_minute low enough so that multiple request per partner
            #       and some manually forced user requests as well as request by the UI e.g.: Auth parnter form
            #       are still covered
            limit = int((max_runtime_in_seconds / 60) * max_requests_per_minute)

            # In case someone sets interval to one second
            limit = 1 if limit <= 0 else limit
        else:
            return False

        # Log start
        logger.info(_("scheduled_set_bpk(): "
                      "Start to process a maximum of %s partner in %s minutes! (max_requests_per_minute: %s)") %
                    (limit, int(max_runtime_in_seconds / 60), max_requests_per_minute))

        # Find partner
        partners_to_update = self.find_bpk_partners_to_update(quick_search=True, limit=limit)

        # Run set BPK per partner until its done or runtime_in_seconds (-2s for safety) reached
        start_datetime = datetime.datetime.now()
        runtime_limit = start_datetime + datetime.timedelta(0, max_runtime_in_seconds - 2)
        partners_done = 0
        for p in partners_to_update:

            # Check if max_runtime_in_seconds -2s is reached
            if datetime.datetime.now() >= runtime_limit:
                logger.error("scheduled_set_bpk(): Could not process all BPK requests in %s seconds" %
                             max_runtime_in_seconds)
                break

            # Run set_bpk for every partner
            try:
                p.set_bpk()
            except Exception as e:
                logger.error("scheduled_set_bpk(): set_bpk() exception for partner %s (ID: %s):\n%s\n" %
                             (p.name, p.id, repr(e)))

            partners_done += 1

        # Log processing info
        logger.info("scheduled_set_bpk() END: Processed %s partner in %.3f second" %
                    (partners_done, time.time() - start_time))

    @api.model
    def scheduled_check_bpk_request_needed(self):
        logger.info(_("check_bpk_request_needed() START"))
        partner_bpk_check_needed = self.find_bpk_partners_to_update(quick_search=False, limit=0)

        if partner_bpk_check_needed:
            bpk_request_needed = fields.datetime.now()

            # Log Info
            logger.warning("Set BPKRequestInProgress for %s partner to %s" %
                           (len(partner_bpk_check_needed), bpk_request_needed))

            # Update partner
            partner_bpk_check_needed.write({'BPKRequestNeeded': bpk_request_needed})

        logger.info(_("check_bpk_request_needed() END"))

    # --------------
    # BUTTON ACTIONS
    # --------------
    # ATTENTION: Button Actions should not have anything else in the interface than 'self' because the mapping
    #            from old api to new api seems not correct for method calls from buttons if any additional positional
    #            or keyword arguments are used!
    # ATTENTION: Button Actions should always use the @api.multi decorator
    @api.multi
    def button_find_bpk_partners_to_update(self):
        self.find_bpk_partners_to_update(quick_search=False, limit=0)
