# -*- coding: utf-8 -*-
import os
from os.path import join as pj
from openerp import api, models, fields
from openerp.exceptions import ValidationError, Warning
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.soap import soap_request, GenericTimeoutError
from openerp.addons.fso_base.tools.name import clean_name
from lxml import etree
import time
import datetime
from datetime import timedelta
from dateutil import tz
import logging
from requests import Timeout
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


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
    @api.multi
    @api.depends('BPKRequestIDS', 'LastBPKRequest', 'BPKRequestNeeded')
    def compute_bpk_state(self):
        count = 0
        start_time = time.time()
        for r in self:
            # Link first BPK record
            r.bpk_id = r.BPKRequestIDS[0].id if r.BPKRequestIDS else None
            # Compute bpk_state
            if r.BPKRequestNeeded:
                r.bpk_state = 'pending'
            elif r.BPKRequestIDS:
                r.bpk_state = r.BPKRequestIDS[0].state
            elif not (all(r[field] for field in self._bpk_regular_fields()) or
                      all(r[field] for field in self._bpk_forced_fields())):
                r.bpk_state = 'data_incomplete'
            # Log information
            count += 1
            if count >= 1000:
                end_time = time.time() - start_time
                logger.info("_compute_bpk_state() "
                            "processed %s records in %3.f sec" % (count, end_time))
                count = 0
                start_time = time.time()

    bpk_state = fields.Selection(selection=[('data_incomplete', 'Data incomplete'),
                                            ('pending', 'BPK Request Needed'),
                                            ('found', 'Found'),
                                            ('found_old', 'Found with old data'),
                                            ('error', 'Error')], readonly=True,
                                 string="BPK-State", compute='compute_bpk_state', compute_sudo=True, store=True)
    bpk_id = fields.Many2one(comodel_name='res.partner.bpk', string="First BPK Record", readonly=True,
                             compute='compute_bpk_state', compute_sudo=True, store=True)
    bpk_id_error_code = fields.Char(related="bpk_id.BPKErrorCode", store=True, readonly=True)
    bpk_id_state = fields.Selection(related="bpk_id.state", store=True, readonly=True)

    @api.onchange('BPKForcedFirstname', 'BPKForcedLastname')
    def onchange_copy_zip_birthdate(self):
        if self.BPKForcedFirstname and self.BPKForcedLastname:
            if not self.BPKForcedZip and self.zip:
                self.BPKForcedZip = self.zip

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

    # Http service error codes
    def _http_service_error_codes(self):
        # 404 = Not Found
        #       The requested resource could not be found but may be available in the future.
        # 408 = Request Timeout
        #       The client did not produce a request within the time that the server was prepared to
        #       wait. The client MAY repeat the request without modifications at any later time.
        # 429 = Too Many Requests
        #       The user has sent too many requests in a given amount of time. Intended for use with
        #       rate-limiting schemes.
        return ['404', '408', '429', '500', '502', '503', '504']

    # ----------------------
    # EXTEND DEFAULT METHODS
    # ----------------------
    @api.model
    def create(self, values, no_bpkrequestneeded_check=False):

        # BPK-Forced-Fields integrity check
        # Check if any BPK forced field has a value
        if any(field for field in self._bpk_forced_fields() if field in values and values[field]):
            assert all(values.get(field, False) for field in self._bpk_forced_fields()), \
                _("All required BPK Forced Fields must be set! Required are: %s" % self._bpk_forced_fields())

        # Check if donation_deduction is disabled
        if values.get('donation_deduction_optout_web', False) or values.get('donation_deduction_disabled', False):
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

        # No Checks if Donation Deduction is going disabled
        # HINT: Manually set BPKRequestNeeded does not matter if donation deduction is disabled
        if vals.get('donation_deduction_optout_web', False) or vals.get('donation_deduction_disabled', False):
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

                # 1.) Skip any further testing if donation deduction is disabled for this partner
                if p.donation_deduction_optout_web or p.donation_deduction_disabled:
                    if p.BPKRequestNeeded:
                        p.BPKRequestNeeded = None
                    continue

                # 2.) Check forced BPK fields for changes if any field with a value is in vals
                if any(field for field in self._bpk_forced_fields() if field in vals and vals[field]):

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
                elif any(field for field in self._bpk_regular_fields() if field in vals and vals[field]):
                    # Make sure all regular fields are set that are required for a bpk request
                    if all(vals.get(field) if field in vals else p[field] for field in self._bpk_regular_fields()):
                        # Check if data has changed
                        if any(vals[field] != p[field] for field in self._bpk_regular_fields() if field in vals):
                            partners_bpk_needed = partners_bpk_needed | p
                        continue

                # 4.) Check optional BPK fields for changes
                elif any(field for field in optional_fields if field in vals and vals[field]):

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
        if not all((firstname, lastname)):
            raise ValidationError(_("Missing input data! Mandatory are firstname and lastname!"))

        # Get the request_data_template path
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                        % soaprequest_templates

        getbpk_template = pj(soaprequest_templates, 'GetBPK_small_j2template.xml')
        assert os.path.exists(getbpk_template), _("GetBPK_small_j2template.xml not found at %s") \
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

                # Store basic data in result
                result['request_data'] = response.request.body
                result['request_url'] = response.request.url
                response_time = time.time() - start_time
                result['response_time_sec'] = "%.3f" % response_time

                # Process response content as xml
                try:
                    assert response.content, _("GetBPK-Request response has no content!")
                    parser = etree.XMLParser(remove_blank_text=True)
                    response_etree = etree.fromstring(response.content, parser=parser)
                    response_pprint = etree.tostring(response_etree, pretty_print=True)
                    result['response_content'] = response_pprint
                except Exception as e:
                    result['response_content'] = response.content
                    result['faultcode'] = response.status_code
                    result['faulttext'] = _("GetBPK-Request response is not valid XML!\n"
                                            "HTML status code %s with reason %s\n\n%s") % (response.status_code,
                                                                                           response.reason,
                                                                                           str(e))
                    # Update answer and process GetBPK for next company
                    responses.append(result)
                    continue

                # Check for http error codes
                if response.status_code != 200:
                    result['response_http_error_code'] = response.status_code
                    result['response_content'] = response_pprint
                    error_code = response_etree.find(".//faultcode")
                    result['faultcode'] = error_code.text if error_code is not None else str(response.status_code)
                    error_text = response_etree.find(".//faultstring")
                    result['faulttext'] = error_text.text if error_text is not None else response.reason
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
                result['faultcode'] = "BPK Request Exception"
                result['faulttext'] = _("BPK Request Exception:\n\n%s\n") % e
                responses.append(result)

        # Assert that all responses for the found companies are either valid or invalid
        # HINT: Must be an error in the ZMR if the identical request data for one company would achieve a different
        #       result for an other company.
        assert all(a['faulttext'] for a in responses) or not any(a['faulttext'] for a in responses), _(
            "Different BPK request results by company with identical request data! ZMR error?")

        return responses

    # -------------
    # MODEL ACTIONS
    # -------------
    # This is a wrapper for _request_bpk() to try multiple requests with different data in case of an request error
    @api.model
    def request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str(), version=False):
        """
        Wrapper for _request_bpk() that will additionally clean names and tries the request multiple times
        with different values depending on the request error
        :param firstname:
        :param lastname:
        :param birthdate:
        :param zipcode:
        :param version: Version of this decision tree schould be raised on any change!
        :return: list(), Containing one result-dict for every company found
                         (at least one result is always in the list ELSE it would throw an exception)
        """
        # Version stored in all BPK-Requests to be checked in bpk_requests_matches_partner_data()
        if version:
            return 1

        # CHECK INPUT DATA
        if not all((firstname, lastname, birthdate)):
            raise ValueError(_("Firstname, Lastname and Birthdate are needed for a BPK request!"))

        # firstname cleanup
        first_clean = clean_name(firstname, split=True)
        if not first_clean:
            first_clean = clean_name(firstname, split=False)
        assert first_clean, _("Firstname is empty after cleanup!")

        # lastname cleanup
        last_clean = clean_name(lastname, split=False)
        assert last_clean, _("Lastname is empty after cleanup!")

        # REQUEST BPK FOR EVERY COMPANY
        # HINT: _request_bpk() will always return at least one result or it would raise an exception
        responses = self._request_bpk(firstname=first_clean, lastname=last_clean, birthdate=birthdate)

        # Return the responses if bpk was found
        if self.response_ok(responses):
            return responses

        # ERROR HANDLING
        # --------------

        # 1.) Person not found at all: Retry with birth-year only
        year = None
        if 'F230' in responses[0].get('faultcode', ""):
            # Try without birthdate but with zipcode
            if zipcode:
                responses = self._request_bpk(firstname=first_clean, lastname=last_clean, birthdate="", zipcode=zipcode)
                if self.response_ok(responses):
                    return responses

            # Try with birth year only
            if 'F230' in responses[0].get('faultcode', ""):
                try:
                    date = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
                    year = date.strftime("%Y")
                except:
                    try:
                        year = str(birthdate).split("-", 1)[0]
                    except:
                        year = None
                if year:
                    responses = self._request_bpk(firstname=first_clean, lastname=last_clean, birthdate=year)

                    # Return list of valid responses
                    if self.response_ok(responses):
                        return responses

                    # If still no person was found we reset the year to none cause no better results can be expected
                    # by a year only search
                    if 'F230' in responses[0].get('faultcode', ""):
                        year = None
            # Since we got no F230 we most likely got multiple person matched after we removed the birthdate
            # Therefore we set the birthdate to none for all the multiple person matched tries to avoid F230 again
            else:
                birthdate = ""

        # 2.) Error: Multiple Persons found: Retry with zipcode
        faultcode = responses[0].get('faultcode', "")
        if zipcode and any(code in faultcode for code in ('F231', 'F233')):
            responses = self._request_bpk(firstname=first_clean, lastname=last_clean, birthdate=year or birthdate,
                                          zipcode=zipcode)

        # 3.) Error: Multiple Persons found: Retry with full firstname (e.g.: second firstname) and zipcode
        faultcode = responses[0].get('faultcode', "")
        if any(code in faultcode for code in ('F231', 'F233')):
            first_clean_nosplit = clean_name(firstname, split=False)
            if first_clean_nosplit != first_clean:
                responses = self._request_bpk(firstname=first_clean_nosplit, lastname=last_clean,
                                              birthdate=year or birthdate, zipcode=zipcode)

        # 4.) Still errors or exceptions: Desperate last try with unchanged data
        if responses[0].get('faultcode', ""):
            rsp_odata = self._request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate, zipcode=zipcode)
            if self.response_ok(rsp_odata):
                return rsp_odata

        return responses

    # Simple response status checker (may be used by java script or by FS)
    @api.model
    def response_ok(self, responses):
        if len(responses) >= 1 and not any(r['faulttext'] for r in responses):
            return True
        else:
            return False

    # Returns the BPK Status for the given request data.
    # HINT: Will first search the existing BPK-Requests and if none found it will send a BPK-Request to the ZMR.
    #       This is useful e.g.: for a java script widget on auth_partner_form
    # Returns a list in the format: [Boolean, {"state": "", "message": ""}]
    @api.model
    def check_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str()):
        # Local helper function
        def _returner(state, msg):
            # state:
            #     bpk_found                     # BPK OK
            #     bpk_not_found                 # Existing BPK-Request or answer from zmr but person could not be found
            #     bpk_multiple_found            # Existing BPK-Request or answer from zmr but multiple person found
            #     bpk_zmr_service_error         # No existing BPK-Request and ZMR service timed out or was unavailable
            #     bpk_exception                 # An exception occured
            # Return list format: [Boolean, {"state": "", "message": ""}]
            # Return dict example: [False, {"state": "exception", "message": "Firstname empty after cleanup!"}]
            ok_states = ['bpk_found']
            error_states = ['bpk_not_found', 'bpk_multiple_found', 'bpk_zmr_service_error', 'bpk_exception']
            assert state in ok_states + error_states, _("check_bpk(): Invalid state: %s" % state)

            # Use a default message if none was provided
            defaut_msg = {'bpk_found': _("Data is valid!"),
                          'bpk_not_found': _("No person matched!"),
                          'bpk_multiple_found': _("Multiple person matched! Please add zip!"),
                          'bpk_zmr_service_error': _("ZMR service not available!"),
                          'bpk_exception': _("Request error"),
                          }
            msg = msg or defaut_msg.get(state, "")

            # Return final list
            return [state in ok_states, {"state": state, "message": msg}]

        # Return result from existing bpk requests
        # ----------------------------------------
        bpk_obj = self.sudo().env['res.partner.bpk']

        # Get the current request logic version
        version = self.request_bpk(version=True)

        # Find a matching positive request for the given data
        positive_dom = [("BPKRequestFirstname", "=", firstname), ("BPKRequestLastname", "=", lastname),
                        ("BPKRequestBirthdate", "=", birthdate), ("BPKPrivate", "!=", False),
                        ("BPKRequestPartnerID.BPKRequestNeeded", "=", False)]
        try:
            positive_req = bpk_obj.search(positive_dom)
            if len(positive_req) >= 1:
                # Return with positive result
                # ATTENTION: This may NOT be correct for different messages for different companies

                # Person was found
                return _returner("bpk_found", positive_req[0].BPKRequestCompanyID.bpk_found)
        except Exception as e:
            logger.error("check_bpk() %s" % str(repr(e)))
            pass

        # Find a matching negative request for the given data
        negative_dom = [("BPKErrorRequestFirstname", "=", firstname), ("BPKErrorRequestLastname", "=", lastname),
                        ("BPKErrorRequestBirthdate", "=", birthdate), ("BPKErrorRequestVersion", "=", version),
                        ("BPKRequestPartnerID.BPKRequestNeeded", "=", False)]
        try:
            negative_req = bpk_obj.search(negative_dom)
            if len(negative_req) >= 1:
                # Return with negative result
                # ATTENTION: This may NOT be correct for different messages for different companies

                # No person matched
                if 'F230' in negative_req[0].BPKErrorCode:
                    return _returner("bpk_not_found", negative_req[0].BPKRequestCompanyID.bpk_not_found)

                # Multiple person matched
                if any(code in negative_req[0].BPKErrorCode for code in ['F231', 'F233']):
                    return _returner("bpk_multiple_found", negative_req[0].BPKRequestCompanyID.bpk_multiple_found)

                # DISABLED: ON GENERIC ERRORS ALWAYS DO THE CHECK e.g.: if the ZMR service was down
                # Other request error or exception
                # HINT: Return all other errors except for ZMR service errors.
                #if not any(e == negative_req[0].BPKErrorCode for e in self._http_service_error_codes()):
                #    return _returner("bpk_exception", negative_req[0].BPKErrorText)
        except Exception as e:
            logger.error("check_bpk() %s" % str(repr(e)))
            pass

        # ZMR BPK-Request
        # ---------------
        try:
            responses = self.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate, zipcode=zipcode)
            assert len(responses) >= 1, _("No responses from request_bpk()!")
        except Exception as e:
            return _returner("bpk_exception", str(repr(e)))

        r = responses[0]
        company = self.sudo().env['res.company'].browse([r.get("company_id")])
        if r.get("private_bpk") or r.get("public_bpk"):
            return _returner("bpk_found", company.bpk_found)
        if 'F230' in r.get("faultcode"):
            return _returner("bpk_not_found", company.bpk_not_found)
        if any(code in r.get("faultcode") for code in ['F231', 'F233']):
            return _returner("bpk_multiple_found", company.bpk_multiple_found)
        if any(err == r.get("faultcode") for err in self._http_service_error_codes()):
            return _returner("bpk_zmr_service_error", r.get("faulttext"))

        # This should only be reached in rare circumstances ;) and serves as a fallback and safety net
        return _returner("bpk_exception", r.get("faulttext"))

    # --------------
    # RECORD ACTIONS
    # --------------
    # Check if the request data matches the partner data
    # TODO: Should be renamed to bpk_requests_matches_partner_data_and_faultcode()
    @api.multi
    def bpk_requests_matches_partner_data(self):
        assert self.ensure_one(), _("bpk_requests_matches_partner_data() is only allowed for one partner at once")
        p = self[0]

        # Get valid bpk companies
        bpk_companies = self._find_bpk_companies()

        # Data is not matching if no BPK Requests to check is available
        if not self.BPKRequestIDS or not [r for r in p.BPKRequestIDS if r.BPKRequestCompanyID.id in bpk_companies.ids]:
            return False

        # Get the res.partner data to compare
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
        # HINT: If any of the BPK Request data does not match the current partner data
        #       OR the error code in any BPK request is unknown (e.g.: service timeout)
        #       we return 'False'
        # ATTENTION: False == u'' will resolve to False! Therefore we use " ... or '' "
        for r in p.BPKRequestIDS:
            # ATTENTION: Only check non orphan bpk records so we do not reinclude them again and again
            if r.BPKRequestCompanyID.id in bpk_companies.ids:

                # Check for unknown errors
                # If the last BPK-Request got an error and the faultcode is unknown return False
                # ATTENTION: For file imports there may not be any error code
                if r.BPKErrorRequestDate > r.BPKRequestData:
                    if not r.BPKErrorCode or not any(code in r.BPKErrorCode for code in ['F230', 'F231', 'F233']):
                        return False

                # Get the latest BPK Request data for comparision
                if r.BPKErrorRequestDate > r.BPKRequestData:
                    # Get Error BPK Request data
                    if r.BPKErrorRequestVersion != self.request_bpk(version=True):
                        return False
                    bpk_data = {'firstname': r.BPKErrorRequestFirstname or '',
                                'lastname': r.BPKErrorRequestLastname or '',
                                'birthdate': r.BPKErrorRequestBirthdate or '',
                                'zipcode': r.BPKErrorRequestZIP or '',
                                }
                else:
                    # Get successful BPK Request data
                    # ATTENTION: Do NOT check the request-logic version number if a BPK was already found and the
                    #            partner data is still the same! Therefore disabled!
                    # if r.BPKRequestVersion != self.request_bpk(version=True):
                    #     return False
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

    @api.multi
    def set_bpk_request_needed(self):
        logger.info("set_bpk_request_needed() for ids %s" % self.ids)
        return self.write({'BPKRequestNeeded': fields.datetime.now()})

    @api.multi
    def remove_bpk_request_needed(self):
        logger.info("remove_bpk_request_needed() for ids %s" % self.ids)
        return self.write({'BPKRequestNeeded': False})

    @api.multi
    def set_bpk(self, force_request=False):
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
        def finish_partner(partner, bpk_request_error=None, bpk_request_needed=None,
                           last_bpk_request=fields.datetime.now()):
            vals = {'BPKRequestNeeded': bpk_request_needed,
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
            # TODO: BETTER IDEA: Check the BPK request if an known error state is included - if not
            #                    redo the request
            if not force_request and p.bpk_requests_matches_partner_data():
                errors[p.id] = _("%s (ID %s): Skipped BPK request! Partner data matches existing BPK request data!") \
                               % (p.name, p.id)
                if not p.LastBPKRequest:
                    finish_partner(p, bpk_request_error=errors[p.id])
                else:
                    finish_partner(p, bpk_request_error=errors[p.id], last_bpk_request=p.LastBPKRequest)
                # Continue with next partner
                continue

            # Stop if donation deduction is disabled
            if p.donation_deduction_optout_web or p.donation_deduction_disabled:
                if p.donation_deduction_optout_web:
                    errors[p.id] = _("%s (ID %s): Donation Deduction Opt Out is set!") % (p.name, p.id)
                if p.donation_deduction_disabled:
                    errors[p.id] = _("%s (ID %s): Donation Deduction Disabled is set!") % (p.name, p.id)
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
            except Timeout as e:
                try:
                    errors[p.id] = _("%s (ID %s): BPK-Request Timeout Exception: %s") % (p.name, p.id, e)
                except:
                    errors[p.id] = _("BPK-Request Timeout Exception")
                logger.info(errors[p.id])
                # ATTENTION: On a timeout we do not clear the BPKRequestNeeded date and do NOT update or create a
                #            res.partner.bpk record so that there will be a retry on the next scheduler run!
                finish_partner(p, bpk_request_error=errors[p.id], bpk_request_needed=p.BPKRequestNeeded)
                continue
            except Exception as e:
                errors[p.id] = _("%s (ID %s): BPK-Request exception: %s") % (p.name, p.id, e)
                logger.info(errors[p.id])
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
                        'BPKRequestVersion': self.request_bpk(version=True),
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
                        'BPKErrorRequestVersion': self.request_bpk(version=True),
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
            # ATTENTION: If the ZMR Service was not available we would get a http_service_error_code. In this case
            #            we would not clear the BPKRequestNeeded date cause we want to retry this partner at the next
            #            scheduler run.
            bpk_request_needed = None
            if any(r.get('faultcode', "") in self._http_service_error_codes() for r in resp):
                bpk_request_needed = p.BPKRequestNeeded
            finish_partner(p, bpk_request_error=faulttext, bpk_request_needed=bpk_request_needed)

            # END: partner for loop

        # Log runtime and error dictionary
        # TODO: do not log single partners any more if error of zombie process could be found (enable if again)
        # if len(self) > 1:
        logger.info("set_bpk(): Processed %s partners in %.3f seconds" % (len(self), time.time()-start_time))
        if errors:
            logger.warning("set_bpk(): Partners with errors: %s" % errors)

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
        # HINT: "donation deduction disabled" and "BPKRequestInProgress" are checked by set_bpk() so we do not
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
        # The goal of the full search is to find any partner that would need an BPK request but BPKRequestNeeded is not
        # set.
        #
        # So contrary to the quick search a full search will not just care about BPKRequestNeeded!
        # Instead it searches
        #    - for all partner without BPKRequestNeeded set but where a bpk request would be possible
        #    - for all partner without BPKRequestNeeded set with existing BPK requests but where:
        #        - bpk requests for companies are missing
        #        - there are too many bpk requests per company
        #        - bpk request data and partner data are not matching

        # Find all companies with fully filled ZMR access fields
        try:
            bpk_companies = self._find_bpk_companies()
        except Exception as e:
            logger.error(_("BPK-NEEDED-FULL-SEARCH: Exception while searching for companies with complete ZMR "
                           "settings:\n%s\n") % e)
            return partners_to_update

        # BASIC SEARCH DOMAIN PARTS
        # ATTENTION: Char Fields (and ONLY Char fields) in odoo domains should be checked with '(not) in', [False, '']
        #            Because the sosyncer v1 may wrote empty strings "" to Char fields instead of False or None
        #
        # Only search for partners
        #     - with donation_deduction_optout_web not set
        #     - with donation_deduction_disabled not set
        #     - with BPKRequestNeeded NOT set
        #     - with full set of regular fields OR full set of forced fields
        #     - where no BPK request is in progress or the BPK request processing start is far in the past or future
        domain += [
            '&', '&', '&', '&',
            ('donation_deduction_optout_web', '=', False),
            ('donation_deduction_disabled', '=', False),
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
        logger.info("BPK-NEEDED-FULL-SEARCH: A.) FIND PARTNERS-TO-UPDATE WITH NO BPK RECORDS FIRST")

        # Create search domain for partners with no existing BPK records
        domain_without_bpk = [('BPKRequestIDS', '=', False)] + domain
        logger.debug("Search domain for partners with no BPK records: %s" % domain_without_bpk)

        # Search for partners with no existing BPK records
        partner_without_bpks = self.env['res.partner'].search(domain_without_bpk, order=order, limit=limit)
        logger.info("BPK-NEEDED-FULL-SEARCH: "
                    "Found %s partners without existing BPK records." % len(partner_without_bpks))

        # STOP AND RETURN: if limit is reached or skip_partner_with_bpk_records is set
        if skip_partner_with_bpk_records or (limit and len(partner_without_bpks) >= limit):
            return partner_without_bpks

        # B.) FIND AND CHECK PARTNERS TO UPDATE WITH EXISTING BPK RECORDS
        # ---------------------------------------------------------------
        # - Find only partners that fulfill the minimum requirements for a bpk check (see base_domain)
        # - Check if latest bpk request data and current partner data are different
        # HINT: If skip_partner_with_bpk_records is set this would be never reached! (Look above: Stopped at point A.)
        # ATTENTION: At some point this search will check !!! ALL !!! partners with BPK records
        #            so make sure to run the full search not too often!
        logger.info("BPK-NEEDED-FULL-SEARCH: B.) FIND PARTNERS-TO-UPDATE WITH EXISTING BPK RECORDS")

        # Use partner_without_bpks as the starting point (may be an empty recordset)
        partners_to_update = partner_without_bpks

        # Create search domain for partners with existing BPK records
        domain_with_bpk = [('BPKRequestIDS', '!=', False)] + domain
        logger.debug("Search domain for partners with BPK records: %s" % domain_with_bpk)

        # CHECK PARTNERS
        # ATTENTION: To load one million res.partner from database to memory takes approximately 30 seconds
        #            Therefore we use batches of fs_batch_size=10000 to optimize read time and memory
        # HINT: remaining -1 = no limit (Check all partners with bpk records)
        offset = 0
        remaining = -1 if not limit else limit - len(partner_without_bpks)
        while remaining:
            partners_to_update_batch_start = len(partners_to_update)

            # Find next partner batch to check
            partner_with_bpks = self.env['res.partner'].search(domain_with_bpk,
                                                               order=order, limit=fs_batch_size, offset=offset)

            # Stop while loop if no partner where found
            if not partner_with_bpks:
                logger.debug("No partners with existing bpk records left to check!")
                break

            # Log info
            logger.info("BPK-NEEDED-FULL-SEARCH: "
                        "Start batch of %s partner to check if a BPK request is needed" % len(partner_with_bpks))

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
                    logger.error(_("BPK-NEEDED-FULL-SEARCH: "
                                   "BPK Records %s found for non existing companies "
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
                    logger.error("BPK-NEEDED-FULL-SEARCH: "
                                 "More than one BPK Record found for the same company for partner %s (ID: %s)" %
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

            # Log batch result
            found_in_batch = len(partners_to_update)-partners_to_update_batch_start
            logger.info("BPK-NEEDED-FULL-SEARCH: "
                        "Found %s partner to update in current batch!" % found_in_batch)

            # PROCEED WITH WHILE LOOP: START NEXT BATCH OF PARTNERS
            # Create search offset for next batch of partners to process
            offset += fs_batch_size

        # Sort the final partner record set
        if partners_to_update:
            partners_to_update = self.env['res.partner'].search([('id', 'in', partners_to_update.ids)], order=order)

        # RETURN THE RECORD SET
        logger.info(_("BPK-NEEDED-FULL-SEARCH: Total partners found requiring a BPK request: %s") %
                    len(partners_to_update))
        return partners_to_update

    @api.model
    def scheduled_set_bpk(self, request_per_minute=10,
                          max_requests_per_minute=120, mrpm_start="17:00", mrpm_end="6:00"):
        start_time = time.time()

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
        assert scheduled_action, \
            _("Scheduled action fso_con_zmr.ir_cron_scheduled_set_bpk not found!")
        assert scheduled_action.interval_type in interval_to_seconds, \
            _("Interval type %s unknown!") % scheduled_action.interval_type

        # Calculate the maximum runtime
        max_runtime_in_seconds = int(scheduled_action.interval_number *
                                     interval_to_seconds[scheduled_action.interval_type])
        max_runtime_in_minutes = int((max_runtime_in_seconds / 60))

        # Limit the number of partners to process based on max_requests_per_minute
        #
        # HINT: set_bpk() may run up to four times per partner per company but it is a save bet to assume
        #       that most of the time one request is enough.
        #
        #       However: Try to set the max_requests_per_minute low enough so that multiple request per partner
        #       and some manually forced user requests as well as request by the UI e.g.: from Auth partner form
        #       java script status widget are still covered
        #
        # ATTENTION: If limit is lower than 1 set it to exactly one partner because a limit of 0 means NO LIMIT !
        #
        # https://stackoverflow.com/questions/10048249/how-do-i-determine-if-current-time-is-within-a-specified-range-using-pythons-da
        #
        number_of_companies = len(self._find_bpk_companies())

        def in_time_period(starttime, endtime, nowtime):
            # Same day
            if starttime < endtime:
                return nowtime >= starttime and nowtime <= endtime
            # Over midnight
            else:
                return nowtime >= starttime or nowtime <= endtime

        def local_time(utc_date_time, from_zone=tz.gettz('UTC'), to_zone=tz.gettz('Europe/Vienna')):
            # ATTENTION: Uses the Austrian timezone because the request rate limit is demanded by the Austrian ZMR.
            # https://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime
            utc_date_time = utc_date_time.replace(tzinfo=from_zone)
            local_date_time = utc_date_time.astimezone(to_zone)
            return local_date_time.time()

        # Local Star_time
        max_req_start = local_time(datetime.datetime.strptime(mrpm_start, "%H:%M"),
                                   from_zone=tz.gettz('Europe/Vienna'), to_zone=tz.gettz('Europe/Vienna'))
        logger.debug("Europe/Vienna Start_time: %s" % max_req_start)

        # Local End_time
        max_req_end = local_time(datetime.datetime.strptime(mrpm_end, "%H:%M"),
                                 from_zone=tz.gettz('Europe/Vienna'), to_zone=tz.gettz('Europe/Vienna'))
        logger.debug("Europe/Vienna End_time: %s" % max_req_end)

        # Local Now_time
        now = local_time(datetime.datetime.now())
        logger.debug("Europe/Vienna Now_time: %s" % now)

        if in_time_period(max_req_start, max_req_end, now):
            limit = int((max_runtime_in_minutes * max_requests_per_minute) / number_of_companies)
        else:
            limit = int((max_runtime_in_minutes * request_per_minute) / number_of_companies)
        limit = 1 if limit < 1 else limit

        # Log start
        logger.info(_("scheduled_set_bpk(): "
                      "START: process a maximum of %s partner in %s minutes") %
                    (limit, max_runtime_in_minutes))

        # Find partner
        logger.info("scheduled_set_bpk(): Run find_bpk_partners_to_update()")
        partners_to_update = self.find_bpk_partners_to_update(quick_search=True,
                                                              search_all_partner=True,
                                                              limit=limit)

        # Run set BPK per partner until its done or runtime_in_seconds (-2s for safety) reached
        runtime_start = datetime.datetime.now()
        runtime_end = runtime_start + datetime.timedelta(0, max_runtime_in_seconds - 22)
        partners_done = 0
        for p in partners_to_update:

            # Check if max_runtime_in_seconds -2s is reached
            if datetime.datetime.now() >= runtime_end:
                logger.error("scheduled_set_bpk(): Stopped by timeout: Could not process all %s partner in %s seconds" %
                             (limit, max_runtime_in_seconds))
                break

            # Run set_bpk for every partner
            try:
                logger.info("scheduled_set_bpk(): Run set_bpk() for %s!" % p.name)
                p.set_bpk()
            except Exception as e:
                logger.error("scheduled_set_bpk(): set_bpk() exception for partner %s (ID: %s):\n%s\n" %
                             (p.name, p.id, repr(e)))

            # Add +1 to partners done just for logging later on
            partners_done += 1

        # Log processing info
        logger.info("scheduled_set_bpk(): END: Processed %s partner in %.3f second" %
                    (partners_done, time.time() - start_time))

    @api.model
    def scheduled_check_and_set_bpk_request_needed(self):
        logger.info(_("scheduled_check_and_set_bpk_request_needed(): START"))
        # Find partner where BPKRequestNeeded is not set but needs to be set
        partner_bpk_check_needed = self.find_bpk_partners_to_update(quick_search=False,
                                                                    search_all_partner=True,
                                                                    limit=0)
        if partner_bpk_check_needed:
            # Set date for log and write
            bpk_request_needed = fields.datetime.now()
            # Log info
            logger.warning("Set BPKRequestNeeded to %s for %s partner" %
                           (bpk_request_needed, len(partner_bpk_check_needed)))
            # Update partner
            partner_bpk_check_needed.write({'BPKRequestNeeded': bpk_request_needed})

    # --------------
    # BUTTON ACTIONS
    # --------------
    # ATTENTION: Button Actions should not have anything else in the interface than 'self' because the mapping
    #            from old api to new api seems not correct for method calls from buttons if any additional positional
    #            or keyword arguments are used!
    # ATTENTION: Button actions must use the @api.multi decorator
    @api.multi
    def action_check_and_set_bpk_request_needed(self):
        # Find partner where BPKRequestNeeded is not set but needs to be set
        partner = self.find_bpk_partners_to_update(quick_search=False, limit=0)
        # Set BPKRequestNeeded to now
        partner.set_bpk_request_needed()

    @api.multi
    def action_set_bpk_request_needed(self):
        self.set_bpk_request_needed()

    @api.multi
    def action_remove_bpk_request_needed(self):
        self.remove_bpk_request_needed()

    @api.multi
    def action_set_bpk(self, force_request=False):
        self.set_bpk(force_request=force_request)

    @api.multi
    def action_recompute_bpk_state(self):
        all_partner = self.search([])
        all_partner.compute_bpk_state()
