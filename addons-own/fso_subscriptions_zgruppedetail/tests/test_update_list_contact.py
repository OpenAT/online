# -*- coding: utf-8 -*-

from openerp.tests import common
import datetime
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
            'birthdate_web': datetime.datetime(1981, 1, 1),
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

    def test_01_contact_update_does_not_change_expiration_if_already_expired(self):
        # Create a new list contact
        # ATTENTION: Always deepcopy the vals dict or computed vals may be added to self.list_contact_vals !
        self.list_contact = self.env['mail.mass_mailing.contact'].create(deepcopy(self.list_contact_vals))

        # Update partner to create a second dummy email
        # this is to satisfy validation when setting the
        # original email invalid
        self.list_contact.personemail_id.partner_id.write(
            {'email': '91FDD90E-C4C5-479A-9C3C-E88246A637A8@test.com'})

        # This gueltig_bis date should be at least 2 days in the past
        expected_gueltig_bis = datetime.datetime.now().date() - datetime.timedelta(days=2)
        # Set the original email invalid
        self.list_contact.personemail_id.write(
            {'gueltig_bis': expected_gueltig_bis})

        # Group gueltig_bis should be same as email gueltig_bis
        actual_group_gueltig_bis = datetime.datetime.strptime(
            self.list_contact.personemailgruppe_id.gueltig_bis, '%Y-%m-%d').date()
        self.assertEqual(actual_group_gueltig_bis, expected_gueltig_bis)

        # Update the list contact, this should not change the group validity
        self.list_contact.write({'title_web': 'dummy'})

        # Group gueltig_bis should still be the same as email gueltig_bis
        actual_group_gueltig_bis = datetime.datetime.strptime(
            self.list_contact.personemailgruppe_id.gueltig_bis, '%Y-%m-%d').date()
        self.assertEqual(actual_group_gueltig_bis, expected_gueltig_bis)

    def test_02_contact_opt_out_does_expire_group(self):
        # Create a new list contact
        # ATTENTION: Always deepcopy the vals dict or computed vals may be added to self.list_contact_vals !
        self.list_contact = self.env['mail.mass_mailing.contact'].create(deepcopy(self.list_contact_vals))
        self.list_contact.write({'opt_out': True})

        expected_gueltig_bis = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        actual_group_gueltig_bis = datetime.datetime.strptime(
            self.list_contact.personemailgruppe_id.gueltig_bis, '%Y-%m-%d').date()
        self.assertEqual(actual_group_gueltig_bis, expected_gueltig_bis)
