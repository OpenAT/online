# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResPartnerSosync(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "base.sosync"]
    # TODO: dbo.Person relation model: FS has a different model to record relations between partners:
    #       develop new addon for FS-O

    # ACTIVE (= Hidden)
    # Hidden is not available in Fundraising Studio therefor delayed until we talk about delete
    #active = fields.Boolean(sosync="True")         # Record is hidden (will not show up by default in any search)

    # RELATED FIELDS
    #parent_id = fields.Many2one(sosync="True")     # Funktioniert jetzt nicht - eventuel auslassen  SPAETER neues relationsmodell fuer res.partner in FSO
    #state_id = fields.Many2one(sosync="True")      # Wird derzeit im FS nicht verwendet - daher kann es ausgelassen werden.

    # NEW:
    bpk_state = fields.Selection(sosync="True")

    gender = fields.Selection(sosync="True")        # TODO: Extend selection list based on FS-Values in FSO GeschlechttypID
    #TODO im DEFFERED: lang = fields.Selection(sosync="True")          # SpracheID in FS wird ueber kuerzel gemapped z.b.: de_DE, en_US

    # -----------------------------------------------------------------------------------------------------------------

    # Standard fields
    #is_company = fields.Boolean(sosync="True")     # Kann nicht gesynced werden derzeit. Spaeter event. ueber PersontypID entweder 101 (natuerliche Person) oder 103 Firma moeglich - ACHTUNG: company_name_web auch beruecksichtigen
    #name = fields.Char(sosync="True")              # Nicht mehr relevant da wir nur ueber firstname und lastname TODO: check for sosync Job creation
    firstname = fields.Char(sosync="True")          # Vorname
    lastname = fields.Char(sosync="True")           # Name
    name_zwei = fields.Char(sosync="True")          # Name2
    phone = fields.Char(sosync="True")              # Festnetznummer # TODO: GL2K hat das falsch verwendet ummappen Andere kontrollieren Joe vermitteln
    mobile = fields.Char(sosync="True")             # Mobilnummer   # !!! TODO: ADD TO SOSYNC V1 !!!
    fax = fields.Char(sosync="True")                # Fax           # !!! NOT IN SOSYNC V1 !!!
    email = fields.Char(sosync="True")              # EMail

    # Kanalsperren
    #opt_out = fields.Boolean(sosync="True")        # Now not in FS needed. No communication wanted by the partner by EMail: Todo: Change Text in Forms to "No unspecific E-Mail" wanted

    # Standard address fields
    # INFO: Wird immer auf die letzte guelteig nicht zeitlich limiertiert adresse gesynced
    #       Falls diese nicht vorhanden ist wird auf die letzte gueltige zeitlich limitierte gesynced
    #       Falls diese auch nicht vorhanden ist wird eine neue zeitlich nicht begrenzte adresse angelegt
    # ATTENTION: In FS muss geklaert werden was passiert wenn eine zeitlich nicht begrnzte gueltige addresse nach einer
    #            zeitlich begrenzten angelegt wird.
    street = fields.Char(sosync="True")
    street_number_web = fields.Char(sosync="True")
    #street2 = fields.Char(sosync="True")               # Nicht in FS vorhanden #
    #TODO im DEFFERED: post_office_box_web = fields.Char(sosync="True")    # Post Box Adresszusatz fuer CH
    city = fields.Char(sosync="True")
    zip = fields.Char(sosync="True")
    country_id = fields.Many2one(sosync="True")         # Gehoert zum Adressblock! Country wird gesynced da alle ISO-Codes bereits in FS vorhanden sind     # TODO: Check if needed in sosync v1 !!! NOT IN SOSYNC V1 !!!

    # Website related fields
    #website_published = fields.Boolean(sosync="True")  # Nicht in FS vorhanden

    # -----------------------------------------------------------------------------------------------------------------
    # FS-Online fields (e.g.: from fso_base)

    # Neue Felder die jetzt noch nicht umgesetzt werden (erst wenn benoetigt von Kunde)
    # TODO: nationality - Will be done later or never :)
    # TODO: Adresszuatz in FS - Ist nicht zuhanden oder Lieferadresse sondern eben ein Adresszusatz. Sobald erster Kunde das mochte machen wir dies

    anrede_individuell = fields.Char(sosync="True")                 # AnredeIndividuell bei Adresse und bei E-Mail
    title_web = fields.Char(sosync="True")                          # Titel
    birthdate_web = fields.Date(sosync="True")                      # Geb. Datum # TODO: Check if timezone may make a day shift in odoo and then in fs
    #TODO im DEFFERED: company_name_web = fields.Char(sosync="True")                   # TODO: Folgebesprechung TODO MIKE: Check wo eingesetzt
    #                  WAS ACTIVATED SINCE WE NEED IT FOR RNDE!
    company_name_web = fields.Char(sosync="True")

    # TODO: Festlegen: Double-Opt-In workflow von FS oder direkt in FSO Wo?
    # TODO: Check current Double Opt in Workflow in FSO
    # TODO: Add an other field to "show" double opt in status
    newsletter_web = fields.Boolean(sosync="True")                  # Newsletter OptIn - Zustimmung generell Newsletter zu empfangen (Mappen auf alle allgem. Newsletter) - Ist nur eine Anmeldung keine Abmeldung wenn er schon E-Mails bekommt

    donation_receipt_web = fields.Boolean(sosync="True")            # Spendenquittung bitte pruefen ob ERstzlos streichbar - TODO: Vorhanden Kunden pruefen wo im Einsatz
    donation_deduction_optout_web = fields.Boolean(sosync="True")   # Spenden nicht autom. absetzen gesetzt vom Spender. TODO: Mit korrekter FS Gruppe verschalten!
    donation_deduction_disabled = fields.Boolean(sosync="True")     # Spenden nicht autom. absetzen gesetzt vom System. TODO: Mit Korrekter FS Gruppe verschalten!      # !!! TODO: ADD TO SOSYNC V1 !!!

    #legal_terms_web = fields.Boolean(sosync="True")                 # Accept legal terms (webshop) derzit nur in FSO

    # BKP Forced Fields
    bpk_forced_firstname = fields.Char(sosync="True")
    bpk_forced_lastname = fields.Char(sosync="True")
    bpk_forced_birthdate = fields.Date(sosync="True")
    bpk_forced_zip = fields.Char(sosync="True")
    bpk_forced_street = fields.Char(sosync="True")
