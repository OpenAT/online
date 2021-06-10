# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp.tools.safe_eval import safe_eval
from openerp import fields
from datetime import datetime
from datetime import timedelta
from openerp.exceptions import ValidationError
from copy import deepcopy

import logging
logger = logging.getLogger(__name__)


class TestMailMassMailingContact(common.TransactionCase):
    def setUp(self):
        super(TestMailMassMailingContact, self).setUp()

        # Default test email address
        # ATTENTION: Must not match any existing e-mail in the database!
        self.email = u'test.email.djkeiu388hhja8h3rh8asdefh@test.com'

        # Create local GroupFolder
        self.groupfolder_email = self.env['frst.zgruppe'].create({
            'tabellentyp_id': '100110',
            'gruppe_kurz': 'Gruppenordner email',
            'gruppe_lang': 'Gruppenordner email',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
        })

        # Create a local Group: group_newsletter
        self.group_newsletter = self.env['frst.zgruppedetail'].create({
            'zgruppe_id': self.groupfolder_email.id,
            'gruppe_kurz': 'Group Newsletter',
            'gruppe_lang': 'Group Newsletter',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
        })

        # Create a mailing list with partner_mandatory and linked to the 'group_newsletter'
        self.mailing_list = self.env['mail.mass_mailing.list'].create({
            'name': u"Test Mailing List",
            'partner_mandatory': True,
            'zgruppedetail_id': self.group_newsletter.id
        })
        self.assertTrue(self.mailing_list.partner_mandatory)

        # Create a country and state
        self.country = self.env['res.country'].create({'name': u"MyTestCountry"})
        self.state = self.env['res.country.state'].create({'name': u"MyTestState",
                                                           'code': u"MTS",
                                                           'country_id': self.country.id})

        # List contact values
        self.list_contact_vals = {
            'list_id': self.mailing_list.id,
            'email': self.email,
            'lastname': u"Lastname A",
            'firstname': u"Firstname B",
            'gender': u"male",
            'anrede_individuell': u"anrede_individuell",
            'title_web': u"title_web",
            'birthdate_web': datetime(1981, 1, 1),
            'newsletter_web': True,
            'phone': u"+43 123456789",
            'mobile': u"+43 660 123456789",
            'street': u"street",
            'street2': u"street 2",
            'street_number_web': u"street_number_web",
            'zip': u"zip",
            'city': u"city",
            'state_id': self.state.id,
            'country_id': self.country.id
        }

    # ATTENTION: Tests have no specific order! Therefore i use the "dumb" method of numbers added!
    # ATTENTION: The setUp() is done individually for every test:
    #            !!! Tests do NOT share the data !!!

    def check_partner_vals(self, partner, list_contact, keys):
        blacklist = ('list_id')
        for field in keys:
            if field in blacklist:
                continue
            if partner[field] != list_contact[field]:
                logger.error("partner[field] '%s' does not match list_contact[field] '%s' for field '%s'"
                             "" % (partner[field], list_contact[field], field))
                return False
        return True

    # Create a new list contact that should create a new partner with a new personemail
    def test_01_create_list_contact_creates_subscription(self):
        # Create a new list contact
        # ATTENTION: Always deepcopy the vals dict or computed vals may be added to self.list_contact_vals !
        self.list_contact = self.env['mail.mass_mailing.contact'].create(deepcopy(self.list_contact_vals))

        # Test if a NEW personemail_id and a NEW partner was created successfully
        self.assertTrue(self.list_contact.personemail_id)
        self.assertEqual(self.list_contact.email, self.list_contact.personemail_id.email)
        self.assertEqual(self.list_contact.email, self.list_contact.personemail_id.partner_id.email)

        # Test if the list contact values where copied to the partner
        self.partner = self.list_contact.personemail_id.partner_id
        self.assertTrue(self.check_partner_vals(self.partner, self.list_contact, self.list_contact_vals.keys()))

        # Test if the subscription (personemailgruppe) was created
        self.assertTrue(self.list_contact.personemailgruppe_id, "Group subscription was not created!")
        self.assertEqual(self.list_contact.personemailgruppe_id.zgruppedetail_id.id,
                         self.group_newsletter.id,
                         "Group of group-subscription is not matching group set in mass mailing list!")
        self.assertEqual(self.list_contact.personemailgruppe_id.frst_personemail_id.id,
                         self.list_contact.personemail_id.id,
                         "E-Mail of list contact is not matching e-mail of group subscription!")

    # Test list contact opt-out transfer to group subscription (personemailgruppe)
    def test_02_list_contact_optout_transfer_to_subscription(self):
        # Create a new list contact
        # ATTENTION: Always deepcopy the vals dict or computed vals may be added to self.list_contact_vals !
        self.list_contact = self.env['mail.mass_mailing.contact'].create(deepcopy(self.list_contact_vals))
        group_subscription = self.list_contact.personemailgruppe_id
        self.assertFalse(self.list_contact.state in ('unsubscribed', 'expired'))

        # List contact opt-out
        self.list_contact.write({'opt_out': True})
        self.assertTrue(self.list_contact.state in ('unsubscribed', 'expired'))
        self.assertTrue(group_subscription.state in ('unsubscribed', 'expired'))
        gueltig_bis = deepcopy(group_subscription.gueltig_bis)

        # Make sure a write to list contact or group subscription will not change state or 'gueltig_bis'
        self.list_contact.write({'lastname': 'write test'})
        group_subscription.write({})
        self.assertTrue(group_subscription.state in ('unsubscribed', 'expired'))
        self.assertTrue(self.list_contact.state in ('unsubscribed', 'expired'))
        self.assertEqual(group_subscription.gueltig_bis, gueltig_bis)

    def test_03_subscription_optout_transfer_to_list_contact(self):
        # Create a new list contact
        # ATTENTION: Always deepcopy the vals dict or computed vals may be added to self.list_contact_vals !
        self.list_contact = self.env['mail.mass_mailing.contact'].create(deepcopy(self.list_contact_vals))
        self.assertFalse(self.list_contact.state in ('unsubscribed', 'expired'))

        # Deactivate the group subscription and therefore the list contact too
        group_subscription = self.list_contact.personemailgruppe_id
        group_subscription.deactivate()
        gueltig_bis = deepcopy(group_subscription.gueltig_bis)
        self.assertTrue(group_subscription.state in ('unsubscribed', 'expired'))
        self.assertTrue(self.list_contact.state in ('unsubscribed', 'expired'))

        # Make sure a write to list contact or group subscription will not change state or 'gueltig_bis'
        self.list_contact.write({'lastname': 'write test'})
        group_subscription.write({})
        self.assertTrue(group_subscription.state in ('unsubscribed', 'expired'))
        self.assertTrue(self.list_contact.state in ('unsubscribed', 'expired'))
        self.assertEqual(group_subscription.gueltig_bis, gueltig_bis)
