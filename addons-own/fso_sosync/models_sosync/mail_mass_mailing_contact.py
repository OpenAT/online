# -*- coding: utf-8 -*-
from openerp import models, fields

import logging
logger = logging.getLogger(__name__)


class MailMassMailingContactSosync(models.Model):
    _name = "mail.mass_mailing.contact"
    _inherit = ["mail.mass_mailing.contact", "base.sosync"]

    list_id = fields.Many2one(sosync="True")
    partner_id = fields.Many2one(sosync="True")
    personemail_id = fields.Many2one(sosync="True")

    # contact
    email = fields.Char(sosync="True")
    firstname = fields.Char(sosync="True")
    lastname = fields.Char(sosync="True")
    gender = fields.Selection(sosync="True")
    anrede_individuell = fields.Char(sosync="True")
    title_web = fields.Char(sosync="True")
    birthdate_web = fields.Date(sosync="True")
    phone = fields.Char(sosync="True")
    mobile = fields.Char(sosync="True")
    newsletter_web = fields.Boolean(sosync="True")

    # address
    street = fields.Char(sosync="True")
    street2 = fields.Char(sosync="True")
    street_number_web = fields.Char(sosync="True")
    zip = fields.Char(sosync="True")
    city = fields.Char(sosync="True")
    state_id = fields.Many2one(sosync="True")       # Not used in FRST
    country_id = fields.Many2one(sosync="True")

    # List Contact approval information
    bestaetigt_am_um = fields.Datetime(sosync="True")
    bestaetigt_typ = fields.Selection(sosync="True")
    bestaetigt_herkunft = fields.Char(sosync="True")
    state = fields.Selection(sosync="True")

    # FRST print fields
    # HINT: Would be great if this could be done "automatically" but right now i could not find a way ...
    #       i know that there is setattr() but i think it needs to be done in the __init__ of the class somehow ?!?
    pf_vorname = fields.Char(sosync="True")
    pf_name = fields.Char(sosync="True")
    pf_anredelower = fields.Char(sosync="True")
    pf_anredekurz = fields.Char(sosync="True")
    pf_anredelang = fields.Char(sosync="True")
    pf_anrede = fields.Char(sosync="True")
    pf_titelnachname = fields.Char(sosync="True")
    pf_email = fields.Char(sosync="True")
    pf_geburtsdatum = fields.Char(sosync="True")

    pf_bank = fields.Char(sosync="True")
    pf_iban_verschluesselt = fields.Char(sosync="True")
    pf_iban = fields.Char(sosync="True")
    pf_bic = fields.Char(sosync="True")
    pf_jahresbeitrag = fields.Char(sosync="True")
    pf_teilbeitrag = fields.Char(sosync="True")
    pf_zahlungsintervall = fields.Char(sosync="True")
    pf_naechstevorlageammonatjahr = fields.Char(sosync="True")
    pf_naechstevorlageam = fields.Char(sosync="True")

    pf_wunschspendenbetrag = fields.Char(sosync="True")
    pf_zahlungsreferenz = fields.Char(sosync="True")
    pf_betragspendenquittung = fields.Char(sosync="True")
    pf_jahr = fields.Char(sosync="True")
    pf_patentier = fields.Char(sosync="True")
    pf_namebeschenkter = fields.Char(sosync="True")
    pf_nameschenker = fields.Char(sosync="True")
    pf_patenkind = fields.Char(sosync="True")
    pf_patenkindvorname = fields.Char(sosync="True")

    pf_bpkvorname = fields.Char(sosync="True")
    pf_bpknachname = fields.Char(sosync="True")
    pf_bpkgeburtsdatum = fields.Char(sosync="True")
    pf_bpkplz = fields.Char(sosync="True")

    pf_personid = fields.Char(sosync="True")

    pf_formularnummer = fields.Char(sosync="True")
    pf_xguid = fields.Char(sosync="True")
    pf_mandatsid = fields.Char(sosync="True")
    pf_emaildatum = fields.Char(sosync="True")


