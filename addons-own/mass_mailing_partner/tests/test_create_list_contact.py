# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp.tools.safe_eval import safe_eval
from openerp import fields
from datetime import datetime
from datetime import timedelta
from openerp.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)


class TestMailMassMailingContact(common.TransactionCase):
    def setUp(self):
        super(TestMailMassMailingContact, self).setUp()

        # Default test email address
        # ATTENTION: Must not match any existing e-mail in the database!
        self.email = u'test.email.djkeiu388hhja8h3rh8asdefh@test.com'

        # Create a mailing list with partner_mandatory
        self.mailing_list = self.env['mail.mass_mailing.list'].create({
            'name': u"Test Mailing List",
            'partner_mandatory': True
        })
        self.assertTrue(self.mailing_list.partner_mandatory)

    # ATTENTION: Tests have no specific order! Therefore i use the "dumb" method of numbers added!
    # ATTENTION: The setUp() is done individually for every test:
    #            !!! Tests do NOT share the data !!!

    # Create a new list contact that should create a new partner with a new personemail
    def test_01_create_list_contact_new_partner(self):
        # Create a new list contact
        self.list_contact = self.env['mail.mass_mailing.contact'].create({
            'list_id': self.mailing_list.id,
            'email': self.email,
            'lastname': u"Lastname A",
            'firstname': u"Firstname B",
        })

        # Test if a NEW personemail_id and a NEW partner was created successfully
        self.assertTrue(self.list_contact.personemail_id)
        self.assertEqual(self.list_contact.email, self.list_contact.personemail_id.email)
        self.assertEqual(self.list_contact.email, self.list_contact.personemail_id.partner_id.email)

        # Test if the list contact values where copied to the partner
        self.partner = self.list_contact.personemail_id.partner_id
        self.assertEqual(self.list_contact.firstname, self.partner.firstname)
        self.assertEqual(self.list_contact.lastname, self.partner.lastname)

    def test_02_create_list_contact_one_existing_personemail(self):
        # Create a new partner
        self.partner = self.env['res.partner'].create({
            'email': self.email,
            'lastname': u"Lastname X",
            'firstname': u"Firstname Y",
        })
        self.assertEqual(self.partner.main_personemail_id.email, self.email)

        # Create a new list contact
        self.list_contact = self.env['mail.mass_mailing.contact'].create({
            'list_id': self.mailing_list.id,
            'email': self.email,
            'lastname': u"Lastname A",
            'firstname': u"Firstname B",
        })

        # Test if the new list contact was linked to the EXISTING personemail
        self.assertEqual(self.list_contact.personemail_id.id, self.partner.main_personemail_id.id)

        # Test that the list contact values where NOT copied to the existing partner
        self.assertNotEqual(self.list_contact.firstname, self.partner.firstname)
        self.assertNotEqual(self.list_contact.lastname, self.partner.lastname)

    def test_03_create_list_contact_multiple_existing_personemail(self):
        # Create a new partner
        self.partner1 = self.env['res.partner'].create({
            'email': self.email,
            'lastname': u"Lastname 1",
            'firstname': u"Firstname 1",
        })
        self.assertEqual(self.partner1.main_personemail_id.email, self.email)

        # Create a second partner with the same e-mail
        self.partner2 = self.env['res.partner'].create({
            'email': self.email,
            'lastname': u"Lastname 2",
            'firstname': u"Firstname 2",
        })
        self.assertEqual(self.partner2.main_personemail_id.email, self.email)

        # Create a new list contact
        self.list_contact = self.env['mail.mass_mailing.contact'].create({
            'list_id': self.mailing_list.id,
            'email': self.email,
            'lastname': u"Lastname A",
            'firstname': u"Firstname B",
        })

        # Test that the new list contact created a new partner since more than one personemail exists for this email
        self.assertNotIn(self.list_contact.personemail_id.partner_id.id, [self.partner1.id, self.partner2.id])

    def test_04_create_list_contact_public_user_logged_in(self):
        # Create a new partner just to test that this partners personemail is NOT linked to the list contact
        self.partner = self.env['res.partner'].create({
            'email': self.email,
            'lastname': u"Lastname 1",
            'firstname': u"Firstname 1",
        })
        self.assertEqual(self.partner.main_personemail_id.email, self.email)

        # Create a new public user.
        public_group_id = self.ref("base.group_public")
        self.public_user = self.env['res.users'].create({
            'login': u'public_test_user_djkiueukja883hkasdasdfe@test.com',
            'name': u'Public Test User',
            "groups_id": [(6, 0, [public_group_id])]
        })
        self.assertTrue(self.public_user.has_group('base.group_public'))
        self.assertFalse(self.public_user.has_group('base.group_user'))
        self.public_user_partner = self.public_user.partner_id

        # Create a new list contact
        self.public_user_env = self.env['mail.mass_mailing.contact'].sudo(user=self.public_user.id)
        self.list_contact = self.public_user_env.create({
            'list_id': self.mailing_list.id,
            'email': self.email,
            'lastname': u"Lastname A",
            'firstname': u"Firstname B",
        })

        # Test that the new list contact has created a new personemail for partner of the logged in public user
        self.assertEqual(self.list_contact.personemail_id.partner_id.id,
                         self.public_user_partner.id)

    def test_05_create_list_contact_regular_user_logged_in(self):
        # Create a new regular user.
        user_group_id = self.ref("base.group_user")
        self.regular_user = self.env['res.users'].create({
            'login': u'public_test_user_djkiueukja883hkasdasdfe@test.com',
            'name': u'Regular Test User',
            "groups_id": [(6, 0, [user_group_id])]
        })
        self.assertTrue(self.regular_user.has_group('base.group_user'))
        self.assertFalse(self.regular_user.has_group('base.group_public'))
        self.regular_user_partner = self.regular_user.partner_id

        # Create a new list contact
        self.regular_user_env = self.env['mail.mass_mailing.contact'].sudo(user=self.regular_user.id)
        self.list_contact = self.regular_user_env.create({
            'list_id': self.mailing_list.id,
            'email': self.email,
            'lastname': u"Lastname A",
            'firstname': u"Firstname B",
        })

        # Test that the new list contact has NOT created a personemail for partner of the logged in regular user
        self.assertNotEqual(self.list_contact.personemail_id.partner_id.id,
                            self.regular_user_partner.id)
