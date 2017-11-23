# -*- coding: utf-8 -*-
import sys
import os
from os.path import join as pj
import openerp
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
# https://wiki.python.org/moin/EscapingXml
from xml.sax.saxutils import escape
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
    BPKForcedFirstname = fields.Char(string="BPK Forced Firstname", index=True)
    BPKForcedLastname = fields.Char(string="BPK Forced Lastname", index=True)
    BPKForcedBirthdate = fields.Date(string="BPK Forced Birthdate", index=True)
    BPKForcedZip = fields.Char(string="BPK Forced ZIP")

    # A Cron jobs that starts every minute will process all partners with BPKRequestNeeded set.
    # HINT: Normally set at res.partner write() (or create()) if any BPK relevant data was set or has changed
    # HINT: Changed from readonly to writeable to allow users to manually force BPK requests
    BPKRequestNeeded = fields.Datetime(string="BPK Request needed", readonly=False, index=True)

    # Store the last BPK Request date also at the partner to make searching for BPKRequestNeeded easier
    LastBPKRequest = fields.Datetime(string="Last BPK Request", readonly=True)

    # In case the BPK request throws an Exception instead of returning a result we store the exception text here
    BPKRequestError = fields.Text(string="BPK Request Exception", readonly=True)

    # Some fields to store BPK information in the res.partner table
    bpk_id = fields.Many2one(comodel_name='res.partner.bpk', string="First BPK Record", readonly=True)
    bpk_id_error_code = fields.Char(string="BPK-Error Code", readonly=True)
    bpk_id_state = fields.Selection(selection=[('found', 'Found'),
                                               ('found_old', 'Found with old data'),
                                               ('error', 'Error')],
                                    string="BPK State", readonly=True)

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

    def _all_bpk_fields(self):
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

    def _zmr_error_codes(self):
        # szr-3.0-anwenderdokumentation_v3_4.pdf
        #
        # "F230"	"Es konnte keine Person im ZMR und/oder ERnP gefunden werden."
        # "F231"	"Es wurden zu viele Personen im ZMR und/oder ERnP gefunden, so dass das Ergebnis nicht eindeutig war. Mit weiteren Suchkriterien kann das Ergebnis noch eindeutig gemacht werden."
        # "F233"	"Dieselbe Ursache wie F231, allerdings mit >5 Treffern."
        #
        # "F401"	"Es fehlt die Rollenberechtigung. Entweder wird im PVP nicht die erforderliche Rolle mit gesendet, oder sie wird vom Anwendungsportal gefiltert."
        # "F402"	"Session-ID wurde nicht mit gesendet. Fuer diese Funktion muss die Session-ID, die in einem vorausgegangen Request geantwortet wurde mit gesendet werden."
        # "F403"	"Mit gesendete Session-ID konnte nicht zugeordnet werden. Es sollte die Session-ID geprueft werden. Ist diese zu alt, muss erneut abgefragt werden."
        # "F404"	"Die Organisation mit dem angegebenen Verwaltungskennzeichen (VKZ) ist nicht fuer den angegebenen Bereich zur Errechnung von bPK berechtigt."
        # "F405"	"Das Verwaltungskennzeichen (VKZ) oder der Bereich fuer die bPK fehlt. Beides sind Pflichtfelder."
        # "F407"	"Es wird ein Behoerdenkennzeichen benoetigt."
        # "F408"	"Ein technische Fehler ist beim Speichern der Session-ID aufgetreten."
        # "F410"	"Ihr VKZ und Ihre ParticipantID duerfen fuer diesen Bereich keine BPKs berechnen"
        # "F411"	"Die Bereiche AS, ZP-TD und GH-GD duerfen nicht unverschluesselt berechnet werden"
        # "F430"	"Fuer eine Personenabfrage muessen neben Familienname und Vorname zumindest ein weiteres Kriterium angegeben werden."
        # "F431"	"Das eingemeldete Geburtsdatum ist ungueltig. Siehe Kapitel 3.1.1."
        # "F432"	"Die Bereichsangabe ist ungueltig. Sie muss immer mit vollstaendigem Praefix erfolgen. zum Beispiel urn:publicid:gv.at:cdid+SA um eine bPK fuer den Bereich SA zu erhalten."
        # "F435"	"Ungueltige Angabe von einem Geschlecht. Gueltige Werte sind male und female."
        # "F436"	"Die Bereichsangabe ist ungueltig. Siehe Kapitel 0"
        # "F438"	"Diese Meldung kommt bei ungueltigen Zeichen im Request. Grundsaetzlich unterstuetzt das SZR, ZMR und ERnP den Zeichensatz UTF-8. Allerdings sind nicht alle Zeichen daraus erlaubt. Wird eines dieser Zeichen zum Beispiel im Familienname mitgesendet, kommt diese Meldung"
        # "F439"	"Es kann nicht mit der bPK fuer einen Bereich gesucht werden, um die bPK einer Person zu einem anderen Bereich zu erhalten. Fragen Sie dazu verschluesselte bPK ab."
        # "F441"	"Das XML-Element Identification muss mit Value und Type gesendet werden, da es sonst als ungueltig angesehen wird."
        # "F450"	"Das gesuchte Geburtsdatum liegt in der Zukunft"
        # "F490"	"Dies ist ein Portalfehler: Zertifikatsueberpruefung fehlgeschlagen (z.B. ungueltige Root-CA, Zertifikat am Portal abgelaufen oder nicht registriert"
        # "F501, F502 und F504"	"Technische Fehler. Nach einiger Zeit erneut versuchen. Sollte die Meldung weiter bestehen, SZR-Support kontaktieren."
        #
        codes = ('F230', 'F231', 'F233')
        return codes

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
        #            This is ONLY useful after BPK file imports in FS.
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
        fields_to_check = [field for field in self._all_bpk_fields() if field in vals]
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

        if not companies:
            logger.warning(_("No company found with complete Austrian ZMR access data!"))
            return companies

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
        # ATTENTION: We do not check other fields at this low level because there may be any combination
        #            e.g.: firstname, lastname, zip
        if not all((firstname, lastname)):
            raise ValidationError(_("Missing input data! Mandatory are firstname and lastname for _request_bpk()!"))

        # Get the request_data_template path and file
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        soaprequest_templates = pj(addon_path, 'soaprequest_templates')
        assert os.path.exists(soaprequest_templates), _("Folder soaprequest_templates not found at %s") \
                                                        % soaprequest_templates

        getbpk_template = pj(soaprequest_templates, 'GetBPK_small_j2template.xml')
        assert os.path.exists(getbpk_template), _("GetBPK_small_j2template.xml not found at %s") \
                                                   % getbpk_template

        # Find all companies with fully filled ZMR access fields
        companies = self._find_bpk_companies()
        assert companies, _("No companies with complete Austrian ZMR access data found!")

        for c in companies:
            # Check if the certificate files still exists at given path and restore them if not
            if not os.path.exists(c.pvpToken_crt_pem_path) or not os.path.exists(c.pvpToken_prvkey_pem_path):
                logger.warning(_("_request_bpk: Certificate data found but files on drive missing. "
                                 "Trying to restore files!"))
                c._certs_to_file()

            # Result interface
            # ATTENTION: Make sure "faulttext" is always filled in case of an BPK error used in request_bpk()
            #            !!! Must also be set for data from file imports !!!
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
                    # HINT: Jump directly to 'except' if there is no content returned
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
                    result['faulttext'] = error_text.text if error_text is not None else response.reason or 'Unknown!'
                    # Update answer and process GetBPK for next company
                    responses.append(result)
                    continue

                # Response is valid
                # HINT: There is a namespace attached which needs to be ignored added or removed before .find()
                #       This is why we use .//*[local-name() in the xPath searches
                #       http://stackoverflow.com/questions/4440451/how-to-ignore-namespaces-with-xpath
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
            "Different BPK request results by company with identical request data! Austrian ZMR error?")

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
        # ATTENTION: This is the current bpk request logic version!
        #            If you change the request_bpk logic make sure to update the version number
        # HINT: Used in last_bpkreq_matches_partner_data()
        if version:
            return 2

        class LogKeeper:
            log = u''

        # HELPER: Do the BPK request and add the request log to the result(s)
        def _request_with_log(first, last, birthd, zipc,):
            # Prepare data
            first = first or u''
            last = last or u''
            birthd = birthd or u''
            zipc = zipc or u''

            # Do the request
            resp = self._request_bpk(firstname=first, lastname=last, birthdate=birthd, zipcode=zipc)

            # Update and append the request log
            try:
                LogKeeper.log += u'Request Data: "'+first+u'"; "'+last+u'"; "'+birthd+u'"; "'+zipc+u'";\n'
                faultcode = resp[0].get('faultcode', u"")
                faulttext = resp[0].get('faulttext', u"")
                if faultcode or faulttext:
                    LogKeeper.log += faultcode+u'\n'+faulttext+u'\n'
                LogKeeper.log += u"----------\n\n"
            except Exception as e:
                logger.error("_request_with_log() Could not store the request log! Unicode error?")
                pass
            for r in resp:
                r['request_log'] = LogKeeper.log

            # Return the response(s)
            return resp

        # CHECK INPUT DATA
        if not all((firstname, lastname, birthdate)):
            raise ValueError(_("request_bpk() Firstname, Lastname and Birthdate are needed for a BPK request!"))

        # firstname cleanup
        first_clean = clean_name(firstname, split=True) or clean_name(firstname, split=False)
        if not first_clean:
            first_clean = firstname
            logger.warning(_("request_bpk() Firstname is empty after cleanup!"))

        # lastname cleanup
        last_clean = clean_name(lastname, split=False)
        if not last_clean:
            last_clean = lastname
            logger.warning(_("request_bpk() Lastname is empty after cleanup!"))

        # Escape invalid XML characters in zip and birthdate
        # HINT: There should be none so the values should not change at all. Still it makes sense as a last resort just
        #       to make sure the xml will not fail with an 500 Error at the ZMR.
        birthdate = escape(birthdate) if birthdate else ''
        zipcode = escape(zipcode) if zipcode else ''

        responses = {}

        # 1.) Try with full birthdate and cleaned names
        responses = _request_with_log(first_clean, last_clean, birthdate, '')
        if self.response_ok(responses):
            return responses

        # 2.) Try with birth year
        try:
            date = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
            year = date.strftime("%Y")
        except:
            try:
                year = str(birthdate).split("-", 1)[0]
            except:
                year = None
        if year:
            # responses = self._request_bpk(firstname=first_clean, lastname=last_clean, birthdate=year)
            responses = _request_with_log(first_clean, last_clean, year, '')
            if self.response_ok(responses):
                return responses

            # ATTENTION: If still no person was found we reset the year to none cause no better results can be expected
            #            by a year only search so all other tries will use the full birthdate
            #            If multiple person where found at this point it makes sense to use the year only for all
            #            subsequent tries cause we already know that the person would not be found with the full
            #            birthdate at this point.
            if 'F230' in responses[0].get('faultcode', ""):
                year = None

        # 3.) Try with zip code
        if zipcode:
            # Without birthdate
            responses = _request_with_log(first_clean, last_clean, '', zipcode)
            if self.response_ok(responses):
                return responses

            # With birthdate or birth year
            responses = _request_with_log(first_clean, last_clean, year or birthdate, zipcode)
            if self.response_ok(responses):
                return responses

        # 4.) Try with full firstname (e.g.: if there is a second firstname that was removed by clean_name())
        # HINT: lastname is never split
        first_clean_nosplit = clean_name(firstname, split=False)
        if first_clean_nosplit and first_clean_nosplit != first_clean:
            responses = _request_with_log(first_clean_nosplit, last_clean, year or birthdate, zipcode)
            if self.response_ok(responses):
                return responses

        # 5.) Last try with nearly unchanged data (only xml-invalid chars will be escaped)
        if not responses or firstname != first_clean or lastname != last_clean:
            # ATTENTION: Since the values are not cleaned we must escape '&', '>' and '<'
            responses = _request_with_log(escape(firstname), escape(lastname), birthdate, zipcode)

        # Finally return the "latest" response(s)
        return responses

    # Simple response status checker (may be used by java script or by FS)
    @api.model
    def response_ok(self, responses):
        # ATTENTION: Make sure "faulttext" is always filled in case of an BPK error in request_bpk()
        #            !!! Must also be set for data from file imports !!!
        if len(responses) >= 1 and not any(r['faulttext'] for r in responses):
            return True
        else:
            return False

    # Returns the BPK Status for the given request data.
    # HINT: Will first search the existing BPK-Requests and if none found it will send a BPK-Request to the ZMR.
    #       This is useful e.g.: for a java script widget on auth_partner_form
    # Returns a list in the format: [Boolean, {"state": "", "message": ""}]
    @api.model
    def check_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str(), internal_search=True):
        # Local helper function
        def _returner(state, msg, log=''):
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
                          'bpk_multiple_found': _("Multiple person matched!"),
                          'bpk_zmr_service_error': _("ZMR service not available!"),
                          'bpk_exception': _("Request error"),
                          }
            msg = msg or defaut_msg.get(state, "")

            # Return final list
            return [state in ok_states, {"state": state, "message": msg, "log": log}]

        # Return result from existing bpk requests
        # ----------------------------------------
        bpk_obj = self.sudo().env['res.partner.bpk']

        # Get the current request logic version
        version = self.request_bpk(version=True)

        # Check the birthdate format
        try:
            b_test = datetime.datetime.strptime(birthdate, '%Y-%m-%d')
        except Exception as e:
            internal_search = False
            logger.warning("check_bpk(): Birhtdate format %s seems incorrect! Internal search skipped!" % birthdate)
            pass

        # Search through existing BPK requests
        if internal_search:
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
                    return _returner("bpk_found", positive_req[0].BPKRequestCompanyID.bpk_found,
                                     log=positive_req[0].bpk_request_log)
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
                        return _returner("bpk_not_found", negative_req[0].BPKRequestCompanyID.bpk_not_found,
                                         log=negative_req[0].bpkerror_request_log)

                    # Multiple person matched
                    if any(code in negative_req[0].BPKErrorCode for code in ['F231', 'F233']):
                        return _returner("bpk_multiple_found", negative_req[0].BPKRequestCompanyID.bpk_multiple_found,
                                         log=negative_req[0].bpkerror_request_log)

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
        r_log = r.get('request_log', '')
        company = self.sudo().env['res.company'].browse([r.get("company_id")])
        if r.get("private_bpk") or r.get("public_bpk"):
            return _returner("bpk_found", company.bpk_found, log=r_log)
        if 'F230' in r.get("faultcode"):
            return _returner("bpk_not_found", company.bpk_not_found, log=r_log)
        if any(code in r.get("faultcode") for code in ['F231', 'F233']):
            return _returner("bpk_multiple_found", company.bpk_multiple_found, log=r_log)
        if any(err == r.get("faultcode") for err in self._http_service_error_codes()):
            return _returner("bpk_zmr_service_error", r.get("faulttext"), log=r_log)

        # This should only be reached in rare circumstances ;) and serves as a fallback and safety net
        return _returner("bpk_exception", r.get("faulttext"), log=r_log)

    # --------------
    # RECORD ACTIONS
    # --------------
    # Computed bpk_state, bpk_id, bpk_id_state, bpk_id_error_code
    @api.multi
    def compute_bpk_state_and_bpk_id(self):
        # HINT: These method is used in set_bpk()!
        #       normally it would be used in create() and write() but in this special case set_bkp() is the better
        #       choice because set_bpk() is the only way how a related bpk record could change it's relevant data
        for r in self:
            vals = {}
            # Link first BPK record and error and state information
            if r.BPKRequestIDS:
                bpk_req = r.BPKRequestIDS[0]
                vals['bpk_id'] = bpk_req.id
                vals['bpk_id_state'] = bpk_req.state
                if bpk_req.BPKErrorRequestDate > bpk_req.BPKRequestDate:
                    vals['bpk_id_error_code'] = bpk_req.BPKErrorCode
                else:
                    vals['bpk_id_error_code'] = None
            else:
                vals['bpk_id'] = None
                vals['bpk_id_state'] = None
                vals['bpk_id_error_code'] = None
            r.write(vals)

    # Check if the request data matches the partner data
    @api.multi
    def last_bpkreq_matches_partner_data(self):
        assert self.ensure_one(), _("last_bpkreq_matches_partner_data() is only allowed for one partner at once")
        p = self[0]

        # Get valid bpk companies
        bpk_companies = self._find_bpk_companies()

        # Data is not matching if no BPK requests exists or BPK requests for valid companies are missing
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
        #
        # ATTENTION: False == u'' will resolve to False! This is why the or '' are set for any field
        #
        for r in p.BPKRequestIDS:

            # ATTENTION: BPK records for deleted companies or companies with removed zmr access data are ignored!
            if r.BPKRequestCompanyID.id in bpk_companies.ids:

                # BPK-Error request is the latest request
                if r.BPKErrorRequestDate > r.BPKRequestDate:

                    # Return False for unknown or missing BPKErrorCode
                    # ATTENTION: For file imports there may not be any error code
                    if not r.BPKErrorCode or not any(code in r.BPKErrorCode for code in ['F230', 'F231', 'F233']):
                        return False

                    # Return False if the request logic version is not matching
                    # HINT: Check version only for BPK Errors
                    if r.BPKErrorRequestVersion != self.request_bpk(version=True):
                        return False

                    # Prepare the error BPK Request data for comparison
                    bpk_data = {'firstname': r.BPKErrorRequestFirstname or '',
                                'lastname': r.BPKErrorRequestLastname or '',
                                'birthdate': r.BPKErrorRequestBirthdate or '',
                                'zipcode': r.BPKErrorRequestZIP or '',
                                }

                # Successful BPK request is the latest request
                else:
                    # Prepare the successful BPK Request data for comparison
                    # ATTENTION: No check of the request logic version if the BPK was already found!
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
    def check_bpk_request_needed(self):
        found_ids = []
        logger.info("check_bpk_request_needed() START ")

        valid_bpk_companies = self._find_bpk_companies()
        # HINT: If there are no companies with Austrian ZMR access data it makes no sense to set BPKRequestNeeded
        if not valid_bpk_companies:
            logger.warning("check_bpk_request_needed() END (No companies with ZMR access data found)")
            return self.env['res.partner']

        counter = 0
        start = time.time()
        for p in self:

            # Logging
            log_batch = 100
            if counter >= log_batch:
                time_per_record = (time.time()-start)/counter
                logger.debug("check_bpk_request_needed() "
                             "done for %s partner (%.3fs/partner) " % (log_batch, time_per_record))
                # Reset counter and time
                counter = 0
                start = time.time()
            counter += 1

            # Check that BPKRequestNeeded is not already set (and other fields that would disable the BPK check)
            if p.BPKRequestNeeded or p.donation_deduction_optout_web or p.donation_deduction_disabled:
                continue

            # Make sure a bpk request is possible (one complete set of mandatory fields is available)
            if not (all(p[field] for field in self._bpk_regular_fields()) or
                    all(p[field] for field in self._bpk_forced_fields())
                    ):
                continue

            # Check for missing BPK records for valid companies or no BPK records at all
            p_bpkrequests_company_ids = [r.BPKRequestCompanyID.id for r in p.BPKRequestIDS]
            if set(valid_bpk_companies.ids) - set(p_bpkrequests_company_ids):
                found_ids.append(p.id)
                continue

            # Check for multiple bpk records for a valid company
            # HINT: This will be corrected in set_bpk()
            # HINT: BPK records for deleted companies or companies with removed zmr access data are ignored
            #       TODO: check if orphan BPK records are also ignored in set_bpk()
            orphan_bpk_ids = set(p_bpkrequests_company_ids) - set(valid_bpk_companies.ids)
            p_bpkrequests_valid_company_ids = [i for i in p_bpkrequests_company_ids if i not in orphan_bpk_ids]
            if len(p_bpkrequests_valid_company_ids) != len(set(p_bpkrequests_valid_company_ids)):
                found_ids.append(p.id)
                continue

            # Check that field 'state' is set for all BPK records
            # HINT: DISABLED since we check the data anyway and after addon install state
            #       is not set for the BPK records until scheduled_compute_bpk_state() has finished
            # if any(not r.state for r in p.BPKRequestIDS):
            #     found = found | p
            #     continue

            # Check if the state of all BPK records is the same
            if len(set([r.state for r in p.BPKRequestIDS])) > 1:
                found_ids.append(p.id)
                continue

            # Check if the BPK request(s) data is different from the partner data
            # HINT: Even if a BPK is already found it would not hurt to do the BPK request again if
            #       any of the relevant fields have changed (it's easier to understand for the user)
            if not p.last_bpkreq_matches_partner_data():
                found_ids.append(p.id)
                continue

        # Return all partner where BPKRequestNeeded should be set but is not right now
        logger.info("check_bpk_request_needed() END")
        return self.browse(found_ids)

    @api.multi
    def set_bpk_request_needed(self):
        logger.info("set_bpk_request_needed() for %s partner" % len(self))
        return self.write({'BPKRequestNeeded': fields.datetime.now()})

    @api.multi
    def remove_bpk_request_needed(self):
        logger.info("remove_bpk_request_needed() for %s partner" % len(self))
        return self.write({'BPKRequestNeeded': False})

    @api.multi
    def set_bpk(self, force_request=False):
        """
        Creates or Updates BPK request for the given partner recordset (=BPKRequestIDS)

        HINT: Runs request_bpk() for every partner.
              Exception text will be written to BPKRequestError if request_bpk() raises one

        ATTENTION: Will also update partner fields: BPKRequestNeeded, LastBPKRequest, BPKRequestError

        :return: dict, partner id and related error if any was found
        """
        # MAKE SURE THERE IST AT LEAST ONE COMPANY WITH FULL ZMR ACCESS DATA
        # ATTENTION: request_bpk() would throw an exception if no company was found and this exception would then
        #            be written to every partner. This is not what we want if there is no company found therefore
        #            we just stop here before we update the partner or their BPK request(s)
        companies = self._find_bpk_companies()

        # HELPER METHOD: FINAL PARTNER UPDATE
        def finish_partner(partner,
                           bpk_request_error=None,
                           bpk_request_needed=None,
                           last_bpk_request=fields.datetime.now()):

            # Update the res.partner fields: BPKRequestNeeded, LastBPKRequest, BPKRequestError
            vals = {'BPKRequestNeeded': bpk_request_needed,
                    'LastBPKRequest': last_bpk_request,
                    'BPKRequestError': bpk_request_error}
            res = partner.write(vals)

            # Compute and update res.partner fields: bpk_state, bpk_id, bpk_id_state, bpk_id_error_code
            partner.compute_bpk_state_and_bpk_id()

            return res

        # GLOBAL ERROR DICTIONARY
        # Format: {partner_id: "Error or exception text", ...}
        errors = dict()

        # BPK REQUEST FOR EACH PARTNER
        # ----------------------------
        start_time = time.time()

        for p in self:
            faulttext = None

            # Stop if donation deduction is disabled (BPKRequestNeeded will be cleared)
            if p.donation_deduction_optout_web or p.donation_deduction_disabled:
                if p.donation_deduction_optout_web:
                    errors[p.id] = _("%s (ID %s): Donation Deduction Opt Out is set!") % (p.name, p.id)
                if p.donation_deduction_disabled:
                    errors[p.id] = _("%s (ID %s): Donation Deduction Disabled is set!") % (p.name, p.id)
                # HINT: We do not change LastBPKRequest if it exits already
                finish_partner(p, bpk_request_error=errors[p.id],
                               last_bpk_request=p.LastBPKRequest or fields.datetime.now())
                continue

            # Stop if the partner data matches the bpk requests data (BPKRequestNeeded will be cleared)
            # HINT: last_bpkreq_matches_partner_data() would return False if no res.partner.bpk records exits!
            # HINT: last_bpkreq_matches_partner_data() would return False if last request was an error and
            #       the request logic version has changed!
            if not force_request and p.last_bpkreq_matches_partner_data():
                errors[p.id] = _("%s (ID %s): Skipped BPK request! Partner data matches existing BPK request data!") \
                               % (p.name, p.id)
                # HINT: We do not change LastBPKRequest if it exits already
                finish_partner(p, bpk_request_error=errors[p.id],
                               last_bpk_request=p.LastBPKRequest or fields.datetime.now())
                # Continue with next partner
                continue

            # Prepare BPK request values
            if any(p[forced_field] for forced_field in self._bpk_forced_fields()):
                firstname = p.BPKForcedFirstname
                lastname = p.BPKForcedLastname
                birthdate_web = p.BPKForcedBirthdate
                zipcode = p.BPKForcedZip
            else:
                firstname = p.firstname
                lastname = p.lastname
                birthdate_web = p.birthdate_web
                zipcode = p.zip


            try:
                start_time = time.time()

                # Do the BPK requests
                resp = self.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate_web,
                                        zipcode=zipcode)
                assert resp, _("%s (ID %s): No BPK-Request response(s)!")

            # Timeout Exception (BPKRequestNeeded stays unchanged)
            except Timeout as e:
                try:
                    errors[p.id] = _("%s (ID %s): BPK-Request Timeout Exception: %s") % (p.name, p.id, e)
                except:
                    errors[p.id] = _("BPK-Request Timeout Exception")
                logger.info(errors[p.id])
                # ATTENTION: On a timeout we do not clear the BPKRequestNeeded date and do NOT update or create a
                #            res.partner.bpk record so that there will be a retry on the next scheduler run!
                finish_partner(p, bpk_request_error=errors[p.id],
                               bpk_request_needed=p.BPKRequestNeeded or fields.datetime.now())
                continue

            # Other Exception (BPKRequestNeeded is set)
            except Exception as e:
                errors[p.id] = _("%s (ID %s): BPK-Request exception: %s") % (p.name, p.id, e)
                logger.info(errors[p.id])
                # ATTENTION: On an exception we do not clear the BPKRequestNeeded date and do NOT update or create a
                #            res.partner.bpk record so that there will be a retry on the next scheduler run!
                finish_partner(p, bpk_request_error=errors[p.id],
                               bpk_request_needed=p.BPKRequestNeeded or fields.datetime.now())
                continue

            # Create or update the res.partner.bpk requests with the responses
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
                        'bpk_request_log': r.get('request_log') or False,
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
                        'bpkerror_request_log': r.get('request_log') or False,
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

                    # Exception on res.partner.bpk deletion (BPKRequestNeeded is set)
                    except Exception as e:
                        errors[p.id] = _("%s (ID %s): More than one BPK record per company found "
                                         "and removal of BPK records failed also: %s") % (p.name, p.id, e)
                        # Update the partner and stop processing other responses but continue with the next partner
                        finish_partner(p, bpk_request_error=errors[p.id],
                                       bpk_request_needed=p.BPKRequestNeeded or fields.datetime.now())
                        break

                # Create a new bpk record or update the existing one
                if bpk:
                    bpk.write(values)
                else:
                    # HINT: This would also update the partner Many2one BPK record field
                    self.env['res.partner.bpk'].sudo().create(values)

                # END: Response processing for loop

            # Finally update the partner after all responses created or updated its bpk requests
            # HINT: We use 'faultcode' only from the last bpk request for this partner but
            #       this should be no problem since all 'faultcode' must be identical

            # We can clear BPKRequestNeeded only if we got a known faultcode or a bpk was found
            bpk_request_needed = p.BPKRequestNeeded or fields.datetime.now()
            r = resp[0]
            faultcode = r.get('faultcode')
            if ((r.get('private_bpk') and r.get('public_bpk')) or (
                faultcode and any(r in faultcode for r in self._zmr_error_codes()))):
                bpk_request_needed = None

            # Update the res.partner
            finish_partner(p, bpk_request_error=faulttext, bpk_request_needed=bpk_request_needed)

            # END: partner for loop

        # Log runtime and error dictionary
        logger.info("set_bpk(): Processed %s partner in %.3f seconds" % (len(self), time.time()-start_time))
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
        # HINT: "donation deduction disabled" is checked by set_bpk() so we do not
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

    def _interval_to_seconds(self):
        return {
            "weeks": 7 * 24 * 60 * 60,
            "days": 24 * 60 * 60,
            "hours": 60 * 60,
            "minutes": 60,
            "seconds": 1
        }

    def _max_runtime_in_seconds(self, action=''):
        scheduled_action = self.env.ref(action)
        assert scheduled_action, _("Scheduled action %s not found!") % action
        interval_to_seconds = self._interval_to_seconds()
        interval_type = scheduled_action.interval_type
        assert interval_type in interval_to_seconds, _("Interval type %s unknown!") % interval_type
        max_runtime_in_seconds = int(scheduled_action.interval_number * interval_to_seconds[interval_type])
        return max_runtime_in_seconds

    @api.model
    def scheduled_set_bpk(self, request_per_minute=10,
                          max_requests_per_minute=120, mrpm_start="17:00", mrpm_end="6:00"):
        start_time = time.time()

        # Calculate the limit of partners to process based on job interval and interval type with 50% safety
        # which means a maximum number of processed partners of 24*60*60/4 = 21600 in 24 hours.
        # HINT: The number of BPK request could be much higher since every partner could cause multiple requests
        #       for multiple companies.

        # Calculate the maximum runtime
        max_runtime_in_seconds = self._max_runtime_in_seconds(action='fso_con_zmr.ir_cron_scheduled_set_bpk')
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
        # HINT: for 200000 records it takes approx 35 min on macbook pro
        #       Make sure limit_time_cpu and limit_time_real is set high enough!
        logger.info(_("scheduled_check_and_set_bpk_request_needed(): START"))

        now = time.time
        domain = [
            '&', '&', '&',
            ('donation_deduction_optout_web', '=', False),
            ('donation_deduction_disabled', '=', False),
            ('BPKRequestNeeded', '=', False),
            '|',
              '&', '&',
              ('firstname', '!=', False),
              ('lastname', '!=', False),
              ('birthdate_web', '!=', False),

              '&', '&',
              ('BPKForcedFirstname', '!=', False),
              ('BPKForcedLastname', '!=', False),
              ('BPKForcedBirthdate', '!=', False),
            ]
        partner_to_check_ids = self.search(domain).ids

        # Start batch processing
        batch_size = 1000
        offset = 0
        total_to_check = len(partner_to_check_ids)
        partner_batch = True
        found_partner_counter = 0
        while_start = now()
        logger.info(_("scheduled_check_and_set_bpk_request_needed(): "
                      "Found a total of %s partner to check in %.6f seconds") % (total_to_check, now()-while_start))
        while partner_batch:
            start = now()

            # Do every batch in its own environment and therefore in an isolated db-transaction
            # HINT: This reduces the RAM and saves all "in between" results if the process should crash
            # You don't need clear caches because is cleared when finish "with"
            with openerp.api.Environment.manage():
                # You don't need close your cr because is closed when finish "with"
                with openerp.registry(self.env.cr.dbname).cursor() as new_cr:

                    # Create a new environment with new cursor database
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)

                    # with_env replaces original env for this method
                    # This forces isolated transaction to commit
                    partner_batch = self.with_env(new_env).browse(partner_to_check_ids[offset:offset + batch_size])

                    offset += batch_size
                    count = len(partner_batch)
                    duration = now() - start
                    logger.info(_("scheduled_check_and_set_bpk_request_needed(): "
                                  "Prefetch %s partner in %.3f seconds (%.3fs/p)") % (count, duration, duration/count))

                    # Check the found partner
                    logger.info(_("scheduled_check_and_set_bpk_request_needed(): Check BPKRequestNeeded for %s partner") % count)
                    start = now()
                    found_partner = partner_batch.check_bpk_request_needed()
                    found_partner_counter += len(found_partner)
                    duration = now() - start
                    tpr = 0 if not count or not duration else duration/count
                    logger.info(_("scheduled_check_and_set_bpk_request_needed(): "
                                  "Checked %s (%s) partner in %.3f seconds (%.3fs/p") % (len(partner_batch), count, duration, tpr))

                    # Update the found partner
                    count = len(found_partner)
                    logger.info(_("scheduled_check_and_set_bpk_request_needed(): "
                                  "Set BPKRequestNeeded for %s found partner") % count)
                    start = now()
                    found_partner.write({'BPKRequestNeeded': fields.datetime.now()})
                    duration = now() - start
                    tpr = 0 if not count or not duration else duration / count
                    logger.info(_("scheduled_check_and_set_bpk_request_needed(): "
                                  "Set BPKRequestNeeded done for %s partner in %.3f seconds (%.3fs/p)") % (
                        count, duration, tpr))

                    # Commit the changes in the new environment
                    new_env.cr.commit()  # Don't show a invalid-commit in this case

            # Log estimated remaining time
            partners_done = offset - batch_size + len(partner_batch)
            total_duration = now() - while_start
            time_per_record = 0 if not partners_done else total_duration / partners_done
            logger.info(_("scheduled_check_and_set_bpk_request_needed(): "
                          "Processed a total of %s partner in %.3f seconds (%.3fs/p)") % (
                            partners_done, total_duration, time_per_record))
            remaining_partner = total_to_check - partners_done
            time_left = remaining_partner * time_per_record
            logger.info("scheduled_check_and_set_bpk_request_needed(): Found %s partner total! "
                        "%s remaining partner to check (approx %.2f minutes left)" % (
                found_partner_counter, remaining_partner, time_left/60))

        logger.info(_("scheduled_check_and_set_bpk_request_needed(): END"))


    @api.model
    def scheduled_compute_bpk_state(self):
        start = time.time()

        # SET LIMIT
        # HINT: We estimate the fastest speed with 10ms per record (Speed on macbook was 16ms)
        max_runtime_sec = self._max_runtime_in_seconds(action='fso_con_zmr.ir_cron_scheduled_compute_bpk_state')
        limit = int((max_runtime_sec * 1000) / 10)

        # GET RECORDS
        records = self.search([('BPKRequestIDS', '!=', False), ('bpk_id', '=', False)], limit=limit)

        # PROCESS RECORDS
        logger.info("scheduled_compute_bpk_state() START compute bpk_state for %s res.partner" % len(records))
        runtime_end = datetime.datetime.now() + datetime.timedelta(0,
                                                                   max_runtime_sec - int(time.time() - start) - 10)
        loop_start = time.time()
        for i, r in enumerate(records):
            # Check remaining runtime
            if datetime.datetime.now() >= runtime_end:
                t = time.time() - loop_start
                logger.info("scheduled_compute_bpk_state() END computed bpk_state for %i res.partner in %.3fs" % (i, t))
                break

            # Make sure the BPK Record(s) state is correct
            r.BPKRequestIDS.compute_state()

            # Recalculate the bpk_state, bkp_id and other fields
            r.compute_bpk_state_and_bpk_id()

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
        found_partner = self.check_bpk_request_needed()
        # Set BPKRequestNeeded to now
        found_partner.set_bpk_request_needed()

    @api.multi
    def action_set_bpk_request_needed(self):
        self.set_bpk_request_needed()

    @api.multi
    def action_remove_bpk_request_needed(self):
        self.remove_bpk_request_needed()

    @api.multi
    def action_set_bpk(self, force_request=False):
        self.set_bpk(force_request=force_request)

