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
from openerp.addons.fso_base.tools.address import clean_street
from lxml import etree
import time
import datetime
from datetime import timedelta
from dateutil import tz
# https://wiki.python.org/moin/EscapingXml
from xml.sax.saxutils import escape
import logging
from requests import Timeout
import copy
import pprint

pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class ResPartnerZMRGetBPK(models.Model):
    _inherit = 'res.partner'

    # Constants
    def bpk_max_tries(self):
        return 20

    # FIELDS
    prevent_donation_deduction = fields.Boolean(string="Prevent Donation Deduction",
                                                help="If set no donation reports can be submitted for this partner!")

    bpk_request_ids = fields.One2many(comodel_name="res.partner.bpk", inverse_name="bpk_request_partner_id",
                                      string="BPK Requests", oldname="BPKRequestIDS")
    # BPK forced request values
    # TODO: Make sure forced BPK fields are always all filled or none (now only done by attr in the form view)
    bpk_forced_firstname = fields.Char(string="BPK Forced Firstname", oldname="BPKForcedFirstname")
    bpk_forced_lastname = fields.Char(string="BPK Forced Lastname", oldname="BPKForcedLastname")
    bpk_forced_birthdate = fields.Date(string="BPK Forced Birthdate", oldname="BPKForcedBirthdate")
    bpk_forced_zip = fields.Char(string="BPK Forced ZIP", oldname="BPKForcedZip")
    bpk_forced_street = fields.Char(string="BPK Forced Street")

    # A Cron jobs that starts every minute will process all partners with bpk_request_needed set.
    # HINT: Normally set at res.partner write() (or create()) if any BPK relevant data was set or has changed
    # HINT: Changed from readonly to writeable to allow users to manually force BPK requests
    # ATTENTION: This was the only index used by the postgresql database
    bpk_request_needed = fields.Datetime(string="BPK Request needed", readonly=False, index=True,
                                         oldname="BPKRequestNeeded")

    # TODO: Add a BPKRequest request counter and update set_bpk() and scheduled_check_and_set_bpk_request_needed() to
    #       honor this counter correctly
    bpk_request_error_tries = fields.Integer(string="BPK Request Error Tries",
                                             help="If bpk_request_error_tries is higher than 20 set_bpk() will just "
                                                  "clear bpk_request_needed and will not try this partner again until "
                                                  "this is lower than 20 again.")

    # Store the last BPK Request date also at the partner to make searching for bpk_request_needed easier
    last_bpk_request = fields.Datetime(string="Last BPK Request", readonly=True, oldname="LastBPKRequest")

    # In case the BPK request throws an Exception instead of returning a result we store the exception text here
    bpk_request_error = fields.Text(string="BPK Request Exception", readonly=True, oldname="BPKRequestError")

    # BPK fields for processing and filtering
    # ---------------------------------------
    # ATTENTION: This fields computes the "global" BPK setting of the partner. This may be overridden by
    #            more specific donor_instruction(s)! Therefore the bpk_state must not always be disabled if this
    #            field is checked!
    bpk_disabled = fields.Boolean(string="BPK Disabled", compute="_compute_bpk_disabled", readonly=True)

    # HINT: Donation Reports will be colored: found and linked: black, found and linked: blue, found and send: green)
    bpk_state = fields.Selection(selection=[
        ('new', 'New'),                                         # No bpk requests and no companies with zmr access data
        ('disabled', 'Donation Deduction Disabled'),            # Disabled for bpk requests (dr grey)
        ('missing_data', 'Missing Data'),                       # Not all required fields set (dr red)
        ('pending', 'BPK Request Needed'),                      # A BPKRequest is needed (dr yellow)
        ('found', 'Found'),                                     # Found with current data (dr black, blue or green)
        ('error_max_tries', 'Error (max retries reached)'),     # Too many tries with unkown error (dr red)
        ('error', 'Error')],                                    # Not found with current partner data (dr red)
        string="BPK State", readonly=True,
        track_visibility='onchange')

    # HINT: Is computed by set_bpk_state()
    bpk_error_code = fields.Char(string="BPK-Error Code", readonly=True)

    # Donation Reports
    donation_report_ids = fields.One2many(string="Donation Reports", readonly=True,
                                          comodel_name="res.partner.donation_report", inverse_name="partner_id")


    @api.depends('donation_deduction_optout_web', 'donation_deduction_disabled')
    def _compute_bpk_disabled(self):
        for r in self:
            r.bpk_disabled = r.donation_deduction_optout_web or r.donation_deduction_disabled

    # Methods to store BPK field names
    def _bpk_regular_fields(self):
        return ['firstname', 'lastname', 'birthdate_web']

    def _bpk_optional_regular_fields(self):
        return ['zip']

    def _bpk_forced_fields(self):
        return ['bpk_forced_firstname', 'bpk_forced_lastname', 'bpk_forced_birthdate']

    def _bpk_optional_forced_fields(self):
        return ['bpk_forced_zip']

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

    def _zmr_error_codes(self, temporary_only=False):
        """
        szr-3.0-anwenderdokumentation_v3_4.pdf

        "F230"	"Es konnte keine Person im ZMR und/oder ERnP gefunden werden."
        "F231"	"Es wurden zu viele Personen im ZMR und/oder ERnP gefunden, so dass das Ergebnis nicht eindeutig war. Mit weiteren Suchkriterien kann das Ergebnis noch eindeutig gemacht werden."
        "F233"	"Dieselbe Ursache wie F231, allerdings mit >5 Treffern."

        "F401"	"Es fehlt die Rollenberechtigung. Entweder wird im PVP nicht die erforderliche Rolle mit gesendet, oder sie wird vom Anwendungsportal gefiltert."
        "F402"	"Session-ID wurde nicht mit gesendet. Fuer diese Funktion muss die Session-ID, die in einem vorausgegangen Request geantwortet wurde mit gesendet werden."
        "F403"	"Mit gesendete Session-ID konnte nicht zugeordnet werden. Es sollte die Session-ID geprueft werden. Ist diese zu alt, muss erneut abgefragt werden."
        "F404"	"Die Organisation mit dem angegebenen Verwaltungskennzeichen (VKZ) ist nicht fuer den angegebenen Bereich zur Errechnung von bPK berechtigt."
        "F405"	"Das Verwaltungskennzeichen (VKZ) oder der Bereich fuer die bPK fehlt. Beides sind Pflichtfelder."
        "F407"	"Es wird ein Behoerdenkennzeichen benoetigt."
        "F408"	"Ein technische Fehler ist beim Speichern der Session-ID aufgetreten."
        "F410"	"Ihr VKZ und Ihre ParticipantID duerfen fuer diesen Bereich keine BPKs berechnen"
        "F411"	"Die Bereiche AS, ZP-TD und GH-GD duerfen nicht unverschluesselt berechnet werden"

        "F430"	"Fuer eine Personenabfrage muessen neben Familienname und Vorname zumindest ein weiteres Kriterium angegeben werden."
        "F431"	"Das eingemeldete Geburtsdatum ist ungueltig. Siehe Kapitel 3.1.1."

        "F432"	"Die Bereichsangabe ist ungueltig. Sie muss immer mit vollstaendigem Praefix erfolgen. zum Beispiel urn:publicid:gv.at:cdid+SA um eine bPK fuer den Bereich SA zu erhalten."
        "F435"	"Ungueltige Angabe von einem Geschlecht. Gueltige Werte sind male und female."
        "F436"	"Die Bereichsangabe ist ungueltig. Siehe Kapitel 0"

        "F438"	"Diese Meldung kommt bei ungueltigen Zeichen im Request. Grundsaetzlich unterstuetzt das SZR, ZMR und ERnP den Zeichensatz UTF-8. Allerdings sind nicht alle Zeichen daraus erlaubt. Wird eines dieser Zeichen zum Beispiel im Familienname mitgesendet, kommt diese Meldung"

        "F439"	"Es kann nicht mit der bPK fuer einen Bereich gesucht werden, um die bPK einer Person zu einem anderen Bereich zu erhalten. Fragen Sie dazu verschluesselte bPK ab."
        "F441"	"Das XML-Element Identification muss mit Value und Type gesendet werden, da es sonst als ungueltig angesehen wird."
        "F450"	"Das gesuchte Geburtsdatum liegt in der Zukunft"

        "F490"	"Dies ist ein Portalfehler: Zertifikatsueberpruefung fehlgeschlagen (z.B. ungueltige Root-CA, Zertifikat am Portal abgelaufen oder nicht registriert"
        "F501, F502 und F504"	"Technische Fehler. Nach einiger Zeit erneut versuchen. Sollte die Meldung weiter bestehen, SZR-Support kontaktieren."


        REQUEST EXCEPTIONS:
        'BPK Request Exception' "We got no answer at all from the ZMR but instead got an exception! This may happen on timeouts or if the ZMR certificate is outdated!"

        :param include_temporal:
        :return:
        """

        if temporary_only:
            # Temporary errors
            temporary_errors = ('F490', 'F501', 'F502', 'F504', 'BPK Request Exception')
            return temporary_errors
        else:
            # Expected (regular) errors
            expected_errors = ('F230', 'F231', 'F233')
            return expected_errors

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
                                                           ('bpk_request_url', '!=', False)])

        if not companies:
            logger.warning(_("No company found with complete Austrian ZMR access data!"))
            return companies

        # Assert that all companies have the same bpk_request_url Setting (Either test or live)
        if len(companies) > 1:
            request_url = companies[0].bpk_request_url
            assert all((c.bpk_request_url == request_url for c in companies)), _("All companies must use the same "
                                                                               "bpk_request_url!")
        return companies

    def _request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str(), street=str(),
                     companies=False):
        """
        Send BPK Request to the Austrian ZMR for every company with complete ZMR access data
        :param firstname:
        :param lastname:
        :param birthdate:
        :param zipcode:
        :param street:
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
        if not companies:
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
                      'request_url': c.bpk_request_url,
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
                response = soap_request(url=c.bpk_request_url,
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
                                                    "DeliveryAddress": {
                                                        "StreetName": street,
                                                    },
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
                    result['faultcode'] = str(response.status_code)
                    result['faulttext'] = _("GetBPK-Request response is not valid XML!\n"
                                            "HTML status code %s with reason %s\n\n%s") % (response.status_code,
                                                                                           response.reason,
                                                                                           str(e))
                    # Update answer and process GetBPK for next company
                    responses.append(result)
                    continue

                # Check for errors
                error_code = response_etree.find(".//faultcode")
                if response.status_code != 200 or error_code is not None:
                    result['response_http_error_code'] = response.status_code
                    result['response_content'] = response_pprint
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
                # ATTENTION: Do not change the faultcode text!!! It is used in _zmr_error_codes()
                result['faultcode'] = "BPK Request Exception"
                result['faulttext'] = _("BPK Request Exception:\n\n%s\n") % e
                responses.append(result)

        # Assert that all responses for the found companies are either valid or invalid
        # HINT: Must be an error in the ZMR if the identical request data for one company would achieve a different
        #       result for an other company.
        assert all(a['faulttext'] for a in responses) or not any(a['faulttext'] for a in responses), _(
            "Different BPK request results by company with identical request data! Austrian ZMR error?")

        return responses

    @api.multi
    def update_donation_reports(self):
        # Search if there are any donation reports to update
        for partner in self:
            donation_reports = self.env['res.partner.donation_report']
            donation_reports = donation_reports.sudo().search(
                [('partner_id', '=', partner.id),
                 ('state', 'in', donation_reports._changes_allowed_states())]
            )
            if donation_reports:
                # HINT: This will run update_state_and_submission_information()
                donation_reports.write({})

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values, no_bpkrequestneeded_check=False):

        # Create the partner in the current environment (memory only right now i guess)
        # ATTENTION: self is still empty but it exits in the 'res' recordset already
        res = super(ResPartnerZMRGetBPK, self).create(values)

        # Compute the bpk state for the partner
        if res:
            res.set_bpk_state()

            # ATTENTION: The update of the donation reports will already be triggered by set_bpk_state() because
            #            it uses the write() method! so no need to include it here

        return res

    @api.multi
    def write(self, values):

        # ATTENTION: !!! After this 'self' is changed (in memory i guess)
        #                'res' is only a boolean !!!
        res = super(ResPartnerZMRGetBPK, self).write(values)

        # Compute the bpk_state and bpk_error_code for the partner
        if not values or 'bpk_state' not in values:
            self.set_bpk_state()

        # Update the donation reports on any bpk_state change
        if res:
            if not values or 'bpk_request_ids' in values or 'bpk_state' in values:
                self.update_donation_reports()

        return res

    @api.multi
    def unlink(self):
        # Prevent the deletion of partners with submitted donation reports
        # ATTENTION: This is needed since we added a cascade delete to the partner_id field.
        #            DELETE's DONE IN SQL ON THE DB WILL NOT CHECK THIS AND WILL DELETE PARTNERS WITH SUBMITTED REPORTS!
        for r in self:
            if any(rep.state not in ['new', 'skipped', 'disabled']
                   for rep in r.donation_report_ids):
                raise ValidationError("Submitted Donation Reports exists for partner %s" % r.id)
        
        return super(ResPartnerZMRGetBPK, self).unlink()

    # -------------
    # MODEL ACTIONS
    # -------------
    # This is a wrapper for _request_bpk() to try multiple requests with different data in case of an request error
    @api.model
    def request_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str(), street=str(), version=False,
                    companies=False):
        """
        Wrapper for _request_bpk() that will additionally clean names and tries the request multiple times
        with different values depending on the request error
        :param firstname:
        :param lastname:
        :param birthdate:
        :param zipcode:
        :param street:
        :param version: Version of this decision tree MUST be raised on any change!
        :param companies: Limit or set the companies with zmr access data for the request. If none are set the request
                          will be done for all companies with zmr access data
        :return: list(), Containing one result-dict for every company found
                         (at least one result is always in the list ELSE it would throw an exception)
        """
        # ATTENTION: This is the current bpk request logic version!
        #            If you change the request_bpk logic make sure to update the version number
        # HINT: Used in all_bpk_requests_matches_partner_data()
        if version:
            return 3

        class LogKeeper:
            log = u''

        # HELPER: Do the BPK request and add the request log to the result(s)
        def _request_with_log(first, last, birthd, zipc, streetn):
            # Prepare data
            first = first or u''
            last = last or u''
            birthd = birthd or u''
            zipc = zipc or u''
            streetn = streetn or u''

            # Do the request
            resp = self._request_bpk(firstname=first, lastname=last, birthdate=birthd, zipcode=zipc, street=streetn,
                                     companies=companies)

            # Update and append the request log
            try:
                LogKeeper.log += u'Request Data: "' + first + u'"; "' + last + u'"; "' + birthd + u'"; "' + \
                                 zipc + u'"; "' + streetn + u'";\n'
            except Exception as e:
                logger.error("Updating the BPK request log failed: %s" % repr(e))
                pass

            try:
                faultcode = resp[0].get('faultcode', u"")
                faulttext = resp[0].get('faulttext', u"")
                if faultcode or faulttext:
                    LogKeeper.log += faultcode + u'\n' + faulttext + u'\n'
                LogKeeper.log += u"Response Time: %s sec\n" % str(resp[0].get('response_time_sec', u"0"))
            except Exception as e:
                logger.error("_request_with_log() Could not store the request log!\n%s") % str(e)
                pass

            LogKeeper.log += u"----------\n\n"

            # Update all results
            for response in resp:
                response['request_log'] = LogKeeper.log

            # Return the response(s)
            return resp

        # CHECK INPUT DATA
        if not all((firstname, lastname, birthdate)):
            raise ValueError(_("request_bpk() Firstname, Lastname and a valid Birthdate are needed for a BPK request!"))

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

        # street cleanup
        if street:
            street = escape(street)
            street = clean_street(street)
            if not street:
                logger.warning("request_bpk() Street is empty after cleanup!")
        else:
            street = ''

        responses_first = {}
        responses = {}

        # 0.) First try with nearly unchanged data
        # HINT: Cleanup will remove just the special chars (or Austrian ZMR will fail with 'non xml valid chars')
        first_basic_clean = clean_name(firstname, full_cleanup=False)
        last_basic_clean = clean_name(lastname, full_cleanup=False)
        responses_first = _request_with_log(first_basic_clean, last_basic_clean, birthdate, zipcode, street)
        if self.response_ok(responses_first):
            return responses_first

        # 1.) Try with full birthdate and cleaned names
        responses = _request_with_log(first_clean, last_clean, birthdate, '', '')
        if self.response_ok(responses):
            return responses

        # 2.) Try with zipcode, full birthdate and cleaned names
        if zipcode:
            responses = _request_with_log(first_clean, last_clean, birthdate, zipcode, '')
            if self.response_ok(responses):
                return responses

        # 3.) Try with birth year only
        try:
            date = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
            year = date.strftime("%Y")
        except:
            try:
                year = str(birthdate).split("-", 1)[0]
            except:
                year = None
        if year:
            responses = _request_with_log(first_clean, last_clean, year, '', '')
            if self.response_ok(responses):
                return responses

        # 4.) Try with zip code only
        if zipcode:
            # Without birthdate
            responses = _request_with_log(first_clean, last_clean, '', zipcode, '')
            if self.response_ok(responses):
                return responses

            # 4.1) Try with zip code and year
            if year:
                responses = _request_with_log(first_clean, last_clean, year, zipcode, '')
                if self.response_ok(responses):
                    return responses

            # 4.2) Try with zip code and street
            if street:
                responses = _request_with_log(first_clean, last_clean, '', zipcode, street)
                if self.response_ok(responses):
                    return responses

        # 5.) Try with full firstname (e.g.: if there is a second firstname that was removed by clean_name())
        # HINT: lastname is never split
        first_clean_nosplit = clean_name(firstname, split=False)
        if first_clean_nosplit and first_clean_nosplit != first_clean:
            responses = _request_with_log(first_clean_nosplit, last_clean, birthdate, zipcode, '')
            if self.response_ok(responses):
                return responses
            # 5.1) Try with full firstname and year
            if year:
                responses = _request_with_log(first_clean_nosplit, last_clean, year, zipcode, '')
                if self.response_ok(responses):
                    return responses
            # 5.2) Try with full firstname, zipcode and street
            if street:
                responses = _request_with_log(first_clean_nosplit, last_clean, '', zipcode, street)
                if self.response_ok(responses):
                    return responses

        # Update log also in responses_first
        for r in responses_first:
            r['request_log'] = LogKeeper.log
        # Finally return the first response (responses_first) with full log
        return responses_first

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
    def check_bpk(self, firstname=str(), lastname=str(), birthdate=str(), zipcode=str(), street=str(),
                  internal_search=True):
        logger.info("check_bpk(): START")

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

            # Log request Time
            logger.info("check_bpk(): ZMR request(s) finished in %.3f seconds" % (time.time() - start_time))
            logger.info("check_bpk(): END")

            # Return final list
            return [state in ok_states, {"state": state, "message": msg, "log": log}]

        # Return result from existing bpk requests
        # ----------------------------------------
        start_time = time.time()
        bpk_obj = self.sudo().env['res.partner.bpk']

        # Get the current request logic version
        version = self.request_bpk(version=True)

        # Check the birthdate format
        try:
            datetime.datetime.strptime(birthdate, '%Y-%m-%d')
        except Exception as e:
            internal_search = False
            logger.warning("check_bpk(): Birhtdate format %s seems incorrect! Internal search skipped!" % birthdate)
            pass

        # Search through existing BPK requests
        if internal_search:

            # Find a matching positive request for the given data
            positive_dom = [("bpk_request_firstname", "=", firstname),
                            ("bpk_request_lastname", "=", lastname),
                            ("bpk_request_birthdate", "=", birthdate),
                            ("bpk_request_zip", "=", zipcode or False),
                            ("bpk_private", "!=", False),
                            ("bpk_request_log", "!=", False)]
            try:
                positive_req = bpk_obj.search(positive_dom, limit=1)
                if len(positive_req) >= 1:
                    # Return with positive result
                    # ATTENTION: This may NOT be correct for different messages for different companies

                    # Person was found
                    log = _("Eine am %s durchgefuehrte BPK Abfrage (ID %s) wurde fuer diese Personendaten "
                            "im System gefunden!\nWenn sie eine erneute Abfrage erzwingen moechten aendern sie bitte "
                            "die Personendaten oder loeschen Sie die im System gespeicherte BPK Anfrage.\n\n"
                            "%s") % (positive_req[0].bpk_request_date,
                                     positive_req[0].id,
                                     positive_req[0].bpk_request_log)
                    return _returner("bpk_found", positive_req[0].bpk_request_company_id.bpk_found,
                                     log=log)
            except Exception as e:
                logger.error("check_bpk() %s" % str(repr(e)))
                pass
            logger.debug("check_bpk(): Internal positive search finished in %.3f seconds" % (time.time() - start_time))

            # Find a matching negative request for the given data
            negative_dom = [("bpk_error_request_firstname", "=", firstname),
                            ("bpk_error_request_lastname", "=", lastname),
                            ("bpk_error_request_birthdate", "=", birthdate),
                            ("bpk_error_request_zip", "=", zipcode or False),
                            ("bpk_error_request_version", "=", version),
                            ("bpk_error_request_log", "!=", False)]
            try:
                negative_req = bpk_obj.search(negative_dom, limit=1)
                if len(negative_req) >= 1:
                    # Return with negative result
                    # ATTENTION: This may NOT be correct for different messages for different companies
                    log = _("Eine am %s durchgefuehrte BPK Abfrage (ID %s) wurde fuer diese Personendaten "
                            "im System gefunden!\nWenn sie eine erneute Abfrage erzwingen moechten aendern sie bitte "
                            "die Personendaten oder loeschen Sie die im System gespeicherte BPK Anfrage.\n\n"
                            "%s") % (negative_req[0].bpk_error_request_date,
                                     negative_req[0].id,
                                     negative_req[0].bpk_error_request_log)

                    # No person matched
                    if 'F230' in negative_req[0].bpk_error_code:
                        return _returner("bpk_not_found", negative_req[0].bpk_request_company_id.bpk_not_found,
                                         log=log)

                    # Multiple person matched
                    if any(code in negative_req[0].bpk_error_code for code in ['F231', 'F233']):
                        return _returner("bpk_multiple_found", negative_req[0].bpk_request_company_id.bpk_multiple_found,
                                         log=log)
            except Exception as e:
                logger.error("check_bpk() %s" % str(repr(e)))
                pass

        # Log internal search time
        logger.info("check_bpk(): Internal search finished in %.3f seconds" % (time.time() - start_time))

        # ZMR BPK-Request
        # ---------------
        start_time = time.time()
        try:
            responses = self.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate, zipcode=zipcode,
                                         street=street)
            assert len(responses) >= 1, _("No responses from request_bpk()!")
        except Exception as e:
            return _returner("bpk_exception", str(repr(e)))

        r = responses[0]
        r_log = r.get('request_log', '')
        r_log = "Es wurden folgende Personendatenkombinationen beim ZMR abgefragt:\n\n" + r_log
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
    @api.multi
    def all_mandatory_bpk_fields_are_set(self):
        """
        Returns True if a all mandatory fields for a BPK request are filled.
        :return:
        """
        assert self.ensure_one(), _("all_mandatory_bpk_fields_are_set() is only allowed for one partner at once")
        # HINT: For r in self is just done for better readability but not really needed since this should only operate
        #       for a single partner: see assert above
        for r in self:
            if any(r[f] for f in self._bpk_forced_fields()):
                if all(r[f] for f in self._bpk_forced_fields()):
                    # TODO: Maybe we should also check here if Birthdate is not in the future?
                    return True
            elif all(r[f] for f in self._bpk_regular_fields()):
                # TODO: Maybe we should also check here if Birthdate is not in the future?
                return True

        return False

    @api.multi
    def all_bpk_requests_matches_partner_data(self, companies=False, bpk_to_check=False):
        """
        Returns True if all latest bpk request fields matches the current partner data fields

        Will return False if no BPK request exits (or none exits for the given companies)
        Will return False if multiple BPK requests exists for any company
        Will return False if the fields of any BPK request do not match the fields of the partner
        Will return False for a request logic mismatch
        Will return False for unknown or temporal errors (missing error code)

        ATTENTION: street field is ignored for this check!

        :param companies: Only compare the bpk requests for given companies
        :return:
        """
        assert self.ensure_one(), _("all_bpk_requests_matches_partner_data() is only allowed for one partner at once")
        p = self[0]

        # Check if there are multiple bpk requests for this partner for one company
        # HINT: This will ignore the given companies and bpk_to_check
        bpk_requests_company_ids = [bpk.bpk_request_company_id.id for bpk in p.bpk_request_ids]
        if bpk_requests_company_ids:
            if len(bpk_requests_company_ids) != len(set(bpk_requests_company_ids)):
                return False

        # Limit BPK requests to check to given bpk requests
        bpk_to_check = bpk_to_check or p.bpk_request_ids

        # Limit BPK requests to check to given companies
        # HINT: If companies are given bpk_to_check from the interface will be ignored/overwritten!
        if companies:
            bpk_request_ids = [bpk.id for bpk in p.bpk_request_ids if bpk.bpk_request_company_id.id in companies.ids]
            bpk_to_check = self.env['res.partner.bpk'].browse(bpk_request_ids)
        if not bpk_to_check:
            return False

        # Prepare the res.partner data to compare
        # ATTENTION: False == u'' will resolve to False! This is why the or '' are set for any field
        if any(p[field] for field in self._bpk_forced_fields()):
            partner_data = {'firstname': p.bpk_forced_firstname or '',
                            'lastname': p.bpk_forced_lastname or '',
                            'birthdate': p.bpk_forced_birthdate or '',
                            'zipcode': p.bpk_forced_zip or '',
                            }
        else:
            partner_data = {'firstname': p.firstname or '',
                            'lastname': p.lastname or '',
                            'birthdate': p.birthdate_web or '',
                            'zipcode': p.zip or '',
                            }

        # Compare the data
        for bpk in bpk_to_check:

            # Last BPK request returned an error: Prepare BPK data from BPKErrorRequest
            if bpk.bpk_error_request_date > bpk.bpk_request_date:

                # Check for unknown errors (without faultcode, may happen for file imports) or temporary errors
                temporal_zmr_error_codes = self._zmr_error_codes(temporary_only=True)
                if not bpk.bpk_error_code or any(code in bpk.bpk_error_code for code in temporal_zmr_error_codes):
                    return False

                # Check the request logic version
                if bpk.bpk_error_request_version != self.request_bpk(version=True):
                    return False
                bpk_data = {'firstname': bpk.bpk_error_request_firstname or '',
                            'lastname': bpk.bpk_error_request_lastname or '',
                            'birthdate': bpk.bpk_error_request_birthdate or '',
                            'zipcode': bpk.bpk_error_request_zip or '',
                            }
            # Last BPK request was successful: Prepare BPK data from BPKRequest
            else:
                bpk_data = {'firstname': bpk.bpk_request_firstname or '',
                            'lastname': bpk.bpk_request_lastname or '',
                            'birthdate': bpk.bpk_request_birthdate or '',
                            'zipcode': bpk.bpk_request_zip or '',
                            }

            # Check the fields for any differences
            if any(partner_data[field] != bpk_data[field] for field in partner_data):
                return False

        # No differences or errors where found: Data matches!
        return True

    # Computed bpk_state
    # TODO: only write info if values did change - and check if this would be faster
    #       (right now we are at 10ms to 12ms)
    @api.multi
    def set_bpk_state(self):
        now = fields.datetime.now

        # Helper method to only write to the partner if values have changed
        # HINT: This comparison is less expensive than real writes to the db
        def write(partner, values):
            # Update the partner
            if any(partner[f] != values[f] for f in values):
                partner.write(values)
            # Update the state of all related bpk records
            if partner.bpk_request_ids:
                partner.bpk_request_ids.set_bpk_state()

        # ATTENTION: The order of the checks is very important e.g. partner data check must be before bpk status check!
        # ATTENTION: Method used in create(), write() and set_bpk()
        #            !!! therefore ALWAYS use write() instead of '=' to prevent recurring write loops !!!
        for r in self:
            # 1.) Check if BPK processing (donation deduction) is disabled
            # ATTENTION: Also check for last donation report for any fiscal year where 'donor_instruction' field is set
            #            to 'submission_forced'. If any is found we must check the bpk because this local setting
            #            overrides the global setting of the res.partner
            if r.bpk_disabled:

                # Check for an individual donor instruction that may overrule the global partner setting for a year
                # ---
                # Get all donor_instructions for this partner
                # HINT: We do not care about the company here i guess? TODO: check if this i ok!
                donor_instructions = self.env['res.partner.donation_report'].search([
                    ('partner_id', '=', r.id),
                    ('submission_env', '=', 'P'),
                    ('donor_instruction', '!=', False),
                ])
                # Check if any last donor_instruction for a meldungs_jahr is a 'submission_forced'
                submission_forced = False
                for y in donor_instructions.mapped('meldungs_jahr'):
                    reps_year = donor_instructions.filtered(lambda rec: rec.meldungs_jahr == y)
                    reps_year_descending = reps_year.sorted(key=lambda rec: rec.anlage_am_um, reverse=True)
                    if reps_year_descending and reps_year_descending[0].donor_instruction == 'submission_forced':
                        submission_forced = True
                        break

                # Update partner if no 'submission_forced' donor instruction was found and bpk_disabled is set
                if not submission_forced:
                    write(r, {'bpk_state': 'disabled', 'bpk_error_code': False, 'bpk_request_needed': False})
                    continue

            # 2.) Check if all mandatory fields for a BPK request are set
            if not r.all_mandatory_bpk_fields_are_set():
                write(r, {'bpk_state': 'missing_data', 'bpk_error_code': False, 'bpk_request_needed': False})
                continue

            # 3.) Check error counter
            if r.bpk_request_error_tries >= self.bpk_max_tries():
                write(r, {'bpk_state': 'error_max_tries', 'bpk_error_code': False, 'bpk_request_needed': False})
                continue

            # 4.) Check bpk_request_needed
            bpk_requests_company_ids = [bpk.bpk_request_company_id.id for bpk in r.bpk_request_ids]
            companies_with_zmr_access = self._find_bpk_companies()

            # 4.1 Check for missing BPK records for companies with zmr access data
            if companies_with_zmr_access:
                if set(companies_with_zmr_access.ids) - set(bpk_requests_company_ids):
                    write(r, {'bpk_state': 'pending', 'bpk_error_code': False, 'bpk_request_needed': now()})
                    continue

            # 4.2 Check for multiple bpk records per company
            if bpk_requests_company_ids:
                if len(bpk_requests_company_ids) != len(set(bpk_requests_company_ids)):
                    logger.error("Multiple BPK-Requests per company found: Partner %s (ID %s)!" % (r.name, str(r.id)))
                    write(r, {'bpk_state': 'pending', 'bpk_error_code': False, 'bpk_request_needed': now()})
                    continue

            # 4.3 Check if the current partner data still matches all bpk requests
            # ATTENTION: THIS WILL ALSO CHECK FOR TEMPORARY ERRORS, REQUEST VERSION AND OTHERS!
            # ATTENTION: This ignores the field 'street'
            if r.bpk_request_ids:
                if not r.all_bpk_requests_matches_partner_data():
                    write(r, {'bpk_state': 'pending', 'bpk_error_code': False, 'bpk_request_needed': now()})
                    continue

            # 5.) Since no BPK request is needed we can set the state by the existing bpk requests
            # ATTENTION: We do not care about companies here!
            #            Each existing BPK request is taken into the equation because each existing bpk request could
            #            be used by an donation report submission!
            if r.bpk_request_ids:
                if all(b.bpk_public and b.bpk_request_date > b.bpk_error_request_date for b in r.bpk_request_ids):
                    write(r, {'bpk_state': 'found', 'bpk_error_code': False, 'bpk_request_needed': False})
                    continue
                else:
                    error_msg = False
                    error_codes = {bpkreq.bpk_error_code or False for bpkreq in r.bpk_request_ids}
                    if error_codes:
                        error_msg = _("Mixed BPK Errors!") if len(error_codes) > 1 else list(error_codes)[0]
                    write(r, {'bpk_state': 'error', 'bpk_error_code': error_msg, 'bpk_request_needed': False})
                    continue

            # 6.) SPECIAL CASE: No BPK requests and no companies with zmr access data
            if not r.bpk_request_ids and not companies_with_zmr_access:
                write(r, {'bpk_state': 'new', 'bpk_error_code': False})
                continue

            # If no state could be determined raise an error!
            raise ValueError(_("%s (ID %id): Partner BPK state could not be computed!") % (r.name, r.id))

        return True

    @api.multi
    def set_bpk(self, force_request=False):
        """
        Creates or Updates BPK request for the given partner recordset (=bpk_request_ids)

        HINT: Runs request_bpk() for every partner.
              Exception text will be written to bpk_request_error if request_bpk() raises one

        ATTENTION: Will also update partner fields: bpk_request_needed, last_bpk_request, bpk_request_error

        :return: dict, partner id and related error if any was found
        """
        now = fields.datetime.now
        errors = dict()

        # BPK REQUEST FOR EACH PARTNER
        # ----------------------------
        start_time = time.time()
        for p in self:
            errors[p.id] = ""

            # TODO: If force_request is set to True we need to completely delete the BPK Request(s) before we compute
            # TODO: the state

            # Check if a BPK request is still needed/possible
            # HINT: This will update the partner bpk_state field
            p.set_bpk_state()
            if not p.bpk_request_needed:
                continue

            # Prepare the request data from the partner
            if any(p[forced_field] for forced_field in self._bpk_forced_fields()):
                firstname = p.bpk_forced_firstname
                lastname = p.bpk_forced_lastname
                birthdate_web = p.bpk_forced_birthdate
                zipcode = p.bpk_forced_zip
                street = p.bpk_forced_street
            else:
                firstname = p.firstname
                lastname = p.lastname
                birthdate_web = p.birthdate_web
                zipcode = p.zip
                street = p.street
            start_time = time.time()

            # Limit the ZMR requests to companies with mismatching bpk requests only
            # TODO: There may be multiple "found" requests per company after an partner merge!
            companies_with_non_matching_requests = self.env['res.company']
            for company in self._find_bpk_companies():
                if not p.all_bpk_requests_matches_partner_data(companies=company):
                    companies_with_non_matching_requests = companies_with_non_matching_requests | company

            # Stop if no company is left
            # ATTENTION: This MUST be an error since p.set_bpk_state() should have cleared bpk_request_needed!
            assert companies_with_non_matching_requests, _("No companies (with ZMR access data) found with "
                                                           "missing BPK requests or with existing BPK requests with"
                                                           "missmatching data. This MUST be an error since "
                                                           "set_bpk_state() should have cleared bpk_request_needed "
                                                           "in this case already!")

            # Request BPK from ZMR
            # --------------------
            try:
                bpk_respones = self.request_bpk(firstname=firstname, lastname=lastname, birthdate=birthdate_web,
                                                zipcode=zipcode, street=street,
                                                companies=companies_with_non_matching_requests)
                assert bpk_respones, _("%s (ID %s): No BPK-Request response(s)!") % (p.name, p.id)
            # 1.) TIMEOUT
            except Timeout as e:
                try:
                    errors[p.id] += _("%s (ID %s): BPK-Request Timeout Exception: %s") % (p.name, p.id, e)
                except:
                    errors[p.id] += _("BPK-Request Timeout Exception")
                # NEXT PARTNER:
                # HINT: last_bpk_request is "increased" to now to stay on top of processing list
                logger.info(errors[p.id])
                p.write({'last_bpk_request': now(),
                         'bpk_request_error': errors[p.id] or False})
                continue
            # 2.) EXCEPTION
            except Exception as e:
                errors[p.id] += _("%s (ID %s): BPK-Request exception: %s") % (p.name, p.id, e)
                # NEXT PARTNER:
                # HINT: last_bpk_request is set. Increase error counter for this unknown error
                logger.info(errors[p.id])
                p.write({'last_bpk_request': now(),
                         'bpk_request_error': errors[p.id] or False,
                         'bpk_request_error_tries': p.bpk_request_error_tries + 1})
                continue

            # 3.) ANSWERS FROM ZMR
            # Create/Update the BPK request(s) for any response(s)
            for resp in bpk_respones:
                try:
                    response_time = float(resp['response_time_sec'])
                except:
                    response_time = float()

                values = {
                    'bpk_request_company_id': resp['company_id'] or False,
                    'bpk_request_partner_id': p.id or False,
                    'last_bpk_request': fields.datetime.now(),
                }
                if resp.get('private_bpk') and resp.get('public_bpk'):
                    values.update({
                        'bpk_private': resp.get('private_bpk') or False,
                        'bpk_public': resp.get('public_bpk') or False,
                        'bpk_request_date': resp.get('request_date') or False,
                        'bpk_request_url': resp.get('request_url') or False,
                        'bpk_request_data': resp.get('request_data') or False,
                        'bpk_request_firstname': firstname or False,
                        'bpk_request_lastname': lastname or False,
                        'bpk_request_birthdate': birthdate_web or False,
                        'bpk_request_zip': zipcode or False,
                        'bpk_request_street': street or False,
                        'bpk_response_data': resp.get('response_content') or False,
                        'bpk_response_time': response_time,
                        'bpk_request_version': self.request_bpk(version=True),
                        'bpk_request_log': resp.get('request_log') or False,
                    })

                else:
                    values.update({
                        'bpk_error_code': resp.get('faultcode') or False,
                        'bpk_error_text': resp.get('faulttext') or False,
                        'bpk_error_request_date': resp.get('request_date') or False,
                        'bpk_error_request_url': resp.get('request_url') or False,
                        'bpk_error_request_data': resp.get('request_data') or False,
                        'bpk_error_request_firstname': firstname or False,
                        'bpk_error_request_lastname': lastname or False,
                        'bpk_error_request_birthdate': birthdate_web or False,
                        'bpk_error_request_zip': zipcode or False,
                        'bpk_error_request_street': street or False,
                        'bpk_error_response_data': resp.get('response_content') or False,
                        'bpk_error_response_time': response_time,
                        'bpk_error_request_version': self.request_bpk(version=True),
                        'bpk_error_request_log': resp.get('request_log') or False,
                    })
                    if values['bpk_error_code'] or values['bpk_error_text']:
                        errors[p.id] += resp.get('faultcode', '') + ' ' + resp.get('faulttext', '')

                # Create/Update the BPK record with the values of this response
                bpk = self.env['res.partner.bpk'].sudo().search([('bpk_request_company_id.id', '=', resp['company_id']),
                                                                 ('bpk_request_partner_id.id', '=', p.id)])

                if not bpk:
                    self.env['res.partner.bpk'].sudo().create(values)
                elif len(bpk) == 1:
                    bpk.write(values)
                else:
                    logger.error("Multiple BPK Request found for partner %s (ID %s) and company with ID %s! Trying to "
                                 "delete existing BPK-Requests %s and create a new one!"
                                 "" % (p.name, str(p.id), resp['company_id'], bpk.ids))
                    try:
                        bpk.unlink()
                    except Exception as e:
                        logger.error("Unlinking of multiple BPKs %s per company failed!" % bpk.ids)
                        raise e
                    logger.info("Unlinking of multiple BPKs was successful! Creating new BPK record!")
                    self.env['res.partner.bpk'].sudo().create(values)

            # NEXT PARTNER:
            # HINT: Reset error counter if no bpk_error_code or the error is known
            error_code = bpk_respones[0].get('bpk_error_code', '')
            error_known = False
            if error_code:
                error_known = any(known_error_code in error_code for known_error_code in self._zmr_error_codes())
            logger.info("set_bpk(): errors: %s" % errors[p.id])
            p.write({'last_bpk_request': now(),
                     'bpk_request_error': errors[p.id] or False,
                     'bpk_request_error_tries': 0 if bpk_respones[0].get('private_bpk', '') or error_known
                                                else p.bpk_request_error_tries + 1,
                     })
            #p.set_bpk_state()
            continue

        # END: partner loop

        # Log and return
        logger.info("set_bpk(): Processed %s partner in %.3f seconds" % (len(self), time.time() - start_time))
        errors = {key: errors[key] for key in errors if errors[key]}
        if errors:
            logger.warning("set_bpk(): Partners with errors: %s" % errors)
        return errors

    # --------------------------------------------
    # (MODEL) ACTIONS FOR AUTOMATED BPK PROCESSING
    # --------------------------------------------
    def _interval_to_seconds(self):
        return {
            "weeks": 7 * 24 * 60 * 60,
            "days": 24 * 60 * 60,
            "hours": 60 * 60,
            "minutes": 60,
            "seconds": 1
        }

    def _max_runtime_in_seconds(self, action=''):
        scheduled_action = self.env.ref(action, raise_if_not_found=False)
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
        # HINT: set_bpk() may run up to n times per partner per company but it is a save bet to assume
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
        logger.info("scheduled_set_bpk(): Search for partners to update")
        partners_to_update = self.search([('bpk_request_needed', '!=', False)],
                                         order='bpk_request_needed DESC', limit=limit)

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
    def scheduled_set_bpk_state(self):
        logger.info(_("scheduled_check_bpk_state(): START"))
        now = time.time

        while_start = now()

        # # TODO: Get the partner field (e.g. firstname) directly from the methods (e.g. _bpk_regular_fields())
        # domain = [
        #     '|',
        #     ('bpk_state', '=', False),
        #     '&', '&', '&', '&',
        #       ('donation_deduction_optout_web', '=', False),
        #       ('donation_deduction_disabled', '=', False),
        #       ('bpk_request_needed', '=', False),
        #       ('bpk_request_error_tries', '<', self.bpk_max_tries()),
        #       '|',
        #       '&', '&',
        #         ('firstname', '!=', False),
        #         ('lastname', '!=', False),
        #         ('birthdate_web', '!=', False),
        #       '&', '&',
        #         ('bpk_forced_firstname', '!=', False),
        #         ('bpk_forced_lastname', '!=', False),
        #         ('bpk_forced_birthdate', '!=', False),
        # ]
        # partner_to_check_ids = self.search(domain).ids

        # Do it for all partner so it will also update all re.partner.bpk state fields!
        partner_to_check_ids = self.search([]).ids

        # Log info about the search
        total_to_check = len(partner_to_check_ids)
        logger.info(_("scheduled_check_bpk_state(): "
                      "Found a total of %s partner to check in %.6f seconds") % (total_to_check, now() - while_start))

        # Start batch processing
        partner_batch = True
        batch_size = 1000
        offset = 0
        while partner_batch:
            start = now()

            # Do every batch in its own environment and therefore in an isolated db-transaction
            # HINT: This reduces the RAM and saves all "in between" results if the process should crash
            # You don't need clear caches because they are cleared when "with" finishes
            with openerp.api.Environment.manage():

                # You don't need close your cr because is closed when finish "with"
                with openerp.registry(self.env.cr.dbname).cursor() as new_cr:

                    # Create a new environment with new cursor database
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                    # HINT: 'with_env' replaces original env for this method
                    #       This forces an isolated transaction to commit
                    partner_batch = self.with_env(new_env).browse(partner_to_check_ids[offset:offset + batch_size])

                    # Increase offset for next batch
                    offset += batch_size

                    # Compute the bpk_state for the found partner
                    found_partner = partner_batch
                    count = len(found_partner)
                    found_partner.set_bpk_state()

                    # Commit the changes in the new environment
                    new_env.cr.commit()  # Don't show a invalid-commit in this case

                    # Log some info for this batch run
                    duration = now() - start
                    tpr = 0 if not count or not duration else duration / count
                    logger.debug(_("scheduled_check_bpk_state(): "
                                   "Set bpk_request_needed done for %s partner in %.3f seconds (%.3fs/p)"
                                   "") % (count, duration, tpr))

            # Log estimated remaining time
            partners_done = offset - batch_size + len(partner_batch)
            total_duration = now() - while_start
            time_per_record = 0 if not partners_done else total_duration / partners_done
            remaining_partner = total_to_check - partners_done
            time_left = remaining_partner * time_per_record
            logger.info(_("scheduled_check_bpk_state(): "
                          "PROCESSED A TOTAL OF %s PARTNER IN %.3f SECONDS (%.3fs/p)! "
                          "%s PARTNER PENDING (approx %.2f minutes left)"
                          "") % (partners_done, total_duration, time_per_record, remaining_partner, time_left / 60))

        logger.info(_("scheduled_check_bpk_state(): END"))

    # --------------
    # BUTTON ACTIONS
    # --------------
    # ATTENTION: Button Actions should not have anything else in the interface than 'self' because the mapping
    #            from old api to new api seems not correct for method calls from buttons if any additional positional
    #            or keyword arguments are used!
    # ATTENTION: Button actions must use the @api.multi decorator
    @api.multi
    def action_set_bpk(self, force_request=False):
        self.set_bpk(force_request=force_request)

    @api.multi
    def action_set_bpk_state(self):
        self.set_bpk_state()
