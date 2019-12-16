# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID, DEFAULT_SERVER_DATE_FORMAT

import logging
logger = logging.getLogger(__name__)


class MailMassMailingContact(models.Model):
    _inherit = "mail.mass_mailing.contact"

    origin = fields.Char(string="Origin", help="Origin information like the web-link, the campaign or similar")

    # partner
    # DONE: Firstname Lastname through separate addon
    gender = fields.Selection(string='Gender', selection=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    anrede_individuell = fields.Char(string='Individuelle Anrede')
    title_web = fields.Char(string='Title Web')
    birthdate_web = fields.Date(string='Birthdate Web')
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    newsletter_web = fields.Boolean(string='Newsletter Web')

    # address
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    street_number_web = fields.Char(string="Street Number Web")
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
    state = fields.Selection(selection=[('approval_pending', 'Waiting for Approval'),
                                        ('subscribed', 'Subscribed'),
                                        ('approved', 'Approved'),
                                        ('unsubscribed', 'Unsubscribed'),
                                        ('expired', 'Expired')],
                             string="State", readonly=True,
                             compute='compute_state', store=True)

    # FRST print fields
    # HINT: Would be great if this could be done "automatically" but right now i could not find a way ...
    #       i know that there is setattr() but i think it needs to be done in the __init__ of the class somehow ?!?
    pf_vorname = fields.Char("Vorname")
    pf_name = fields.Char("Nachname")
    pf_anredelower = fields.Char("Name")
    pf_anredekurz = fields.Char("AnredeKurz")
    pf_anredelang = fields.Char("AnredeLang")
    pf_anrede = fields.Char("Anrede")
    pf_anredetitel = fields.Char("Anredetitel")
    pf_titel = fields.Char("Titel")
    pf_titelnachgestellt = fields.Char("TitelNachgestellt")
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

    @api.multi
    def new_partner_vals(self):
        partner_vals = super(MailMassMailingContact, self).new_partner_vals()
        partner_vals.update({
            'gender': self.gender,
            'anrede_individuell': self.anrede_individuell,
            'title_web': self.title_web,
            'birthdate_web': self.birthdate_web,
            'newsletter_web': self.newsletter_web,
            'phone': self.phone,
            'mobile': self.mobile,
            'street': self.street,
            'street2': self.street2,
            'street_number_web': self.street_number_web,
            'zip': self.zip,
            'city': self.city,
            'state_id': self.state_id,
            'country_id': self.country_id})
        return partner_vals

    @api.depends('opt_out', 'list_id.bestaetigung_erforderlich', 'bestaetigt_am_um')
    def compute_state(self):
        for r in self:
            if r.opt_out:
                state = 'unsubscribed'
            elif r.list_id.bestaetigung_erforderlich and not r.bestaetigt_am_um:
                state = 'approval_pending'
            else:
                state = 'approved' if r.bestaetigt_am_um else 'subscribed'

            # Write state
            if r.state != state:
                r.state = state
