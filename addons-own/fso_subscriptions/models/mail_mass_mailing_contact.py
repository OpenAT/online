# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID

import logging
logger = logging.getLogger(__name__)


class MailMassMailingContact(models.Model):
    _inherit = "mail.mass_mailing.contact"

    # TODO: Firstname Lastname
    # TODO: mass_mailing_partner > Do not change the list contact data if the partner changes - the goal is to keep
    #       the original values of the subscription (also much better for partner merges)
    # TODO: The approval fields should be added to an abstract model - to much code replication right now - we could
    #       add a class variable for the selection field e.g.: _bestaetigt_typ = [('doubleoptin', 'DoubleOptIn')]
    #       so we could "configure" this field by class if needed

    # contact
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")

    # address
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    zip = fields.Char(string="Zip")
    city = fields.Char(string="City")
    state_id = fields.Many2one(string="State", comodel_name="res.country.state", ondelete='restrict')
    country_id = fields.Many2one(string="Country", comodel_name="res.country")

    # List Contact approval information
    bestaetigt_am_um = fields.Datetime("Bestaetigt", readonly=True)
    bestaetigt_typ = fields.Selection(selection=[('doubleoptin', 'DoubleOptIn')],
                                        string="Bestaetigungs Typ", readonly=True)
    bestaetigt_herkunft = fields.Char("Bestaetigungsherkunft", readonly=True,
                                      help="E.g.: The link or the workflow process")

    # FRST print fields
    # HINT: Would be great if this could be done "automatically" but right now i could not find a way ...
    #       i know that there is setattr() but i think it needs to be done in the __init__ of the class somehow ?!?
    pf_vorname = fields.Char("Vorname")
    pf_name = fields.Char("Nachname")
    pf_anredelower = fields.Char("Name")
    pf_anredekurz = fields.Char("AnredeKurz")
    pf_anredelang = fields.Char("AnredeLang")
    pf_anrede = fields.Char("Anrede")
    pf_titelnachname = fields.Char("TitelNachname")
    pf_email = fields.Char("Email")
    pf_geburtsdatum = fields.Char("Geburtsdatum")

    pf_bank = fields.Char("Bank")
    pf_iban_verschluesselt = fields.Char("IBAN_Verschluesselt")
    pf_iban = fields.Char("IBAN")
    pf_bic = fields.Char("BIC")
    pf_jahresbeitrag = fields.Char("Jahresbeitrag")
    pf_teilbeitrag = fields.Char("Teilbeitrag")
    pf_zahlungsintervall = fields.Char("Zahlungsintervall")
    pf_naechstevorlageammonatjahr = fields.Char("NaechsteVorlageAmMonatJahr")
    pf_naechstevorlageam = fields.Char("NaechsteVorlageAm")

    pf_wunschspendenbetrag = fields.Char("WunschSpendenbetrag")
    pf_zahlungsreferenz = fields.Char("Zahlungsreferenz")
    pf_betragspendenquittung = fields.Char("BetragSpendenquittung")
    pf_jahr = fields.Char("Jahr")
    pf_patentier = fields.Char("Patentier")
    pf_namebeschenkter = fields.Char("NameBeschenkter")
    pf_nameschenker = fields.Char("NameSchenker")
    pf_patenkind = fields.Char("Patenkind")
    pf_patenkindvorname = fields.Char("PatenkindVorname")

    pf_bpkvorname = fields.Char("BPKVorname")
    pf_bpknachname = fields.Char("BPKNachName")
    pf_bpkgeburtsdatum = fields.Char("BPKGeburtsdatum")
    pf_bpkplz = fields.Char("BPKPLZ")

    pf_personid = fields.Char("PersonID")

    pf_formularnummer = fields.Char("Formularnummer")
    pf_xguid = fields.Char("xGuid")
    pf_mandatsid = fields.Char("MandatsID")
    pf_emaildatum = fields.Char("Emaildatum")


