# -*- coding: utf-8 -*-

from openerp import fields
from openerp.tests import common
from openerp.exceptions import AccessError, ValidationError

from datetime import datetime
from datetime import timedelta

import logging
logger = logging.getLogger(__name__)


class TestFRSTSubscriptionSecurity(common.TransactionCase):
    def setUp(self):
        super(TestFRSTSubscriptionSecurity, self).setUp()

        # Create local GroupFolder
        self.groupfolder_email = self.env['frst.zgruppe'].create({
            'tabellentyp_id': '100110',
            'gruppe_kurz': 'Gruppenordner email',
            'gruppe_lang': 'Gruppenordner email',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
            # Only users in the sosync usergroup are able to create, modify or unlink group subscriptions
            'gui_gruppen_bearbeiten_moeglich': False,
            'nur_eine_gruppe_anmelden': True,
        })

        # Create a local Group: group_newsletter
        self.group_newsletter = self.env['frst.zgruppedetail'].create({
            'zgruppe_id': self.groupfolder_email.id,
            'gruppe_kurz': 'Group Newsletter',
            'gruppe_lang': 'Group Newsletter',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
        })

        self.group_newsletter_b = self.env['frst.zgruppedetail'].create({
            'zgruppe_id': self.groupfolder_email.id,
            'gruppe_kurz': 'Group Newsletter B',
            'gruppe_lang': 'Group Newsletter B',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
        })

        # Create Partner 1 with a PersonEmail
        self.partner_max1 = self.env['res.partner'].create({
            'name': u"Max1 Mustermann",
            'email': u"max@test.com"
        })

        # Create an backend user with group manager rights
        group_manager_id = self.ref("fso_frst_groups.group_fs_group_manager")
        self.backend_user = self.env['res.users'].create({
            'login': u'backend_test_user_djkiueukja883hkasdasdfe@test.com',
            'name': u'Backend Test User',
            "groups_id": [(6, 0, [group_manager_id])]
        })

        # Create a sosync user
        sosync_group_id = self.ref("base.sosync")
        self.sosync_user = self.env['res.users'].create({
            'login': u'sosync_test_user_djkfsodf3hkasdasdfe@test.com',
            'name': u'Sosync Test User',
            "groups_id": [(6, 0, [sosync_group_id])]
        })

    def test_01_restrict_create_subscription_for_backend_users(self):
        """ Create subscription for group in restricted group folder as backend user and admin user """
        with self.assertRaises(AccessError):
            subscription = self.env['frst.personemailgruppe'].sudo(user=self.backend_user).create({
                'zgruppedetail_id': self.group_newsletter.id,
                'frst_personemail_id': self.partner_max1.main_personemail_id.id,
            })
        with self.assertRaises(AccessError):
            subscription = self.env['frst.personemailgruppe'].sudo().create({
                'zgruppedetail_id': self.group_newsletter.id,
                'frst_personemail_id': self.partner_max1.main_personemail_id.id,
            })

    def test_02_restrict_write_subscription_for_backend_users(self):
        """ Write subscription for group in restricted group folder as backend user and admin user """
        subscription = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        self.assertTrue(subscription.exists())
        # Backend User
        with self.assertRaises(AccessError):
            subscription.sudo(user=self.backend_user).write({'gueltig_von': fields.datetime.now()})
        # Admin User
        with self.assertRaises(AccessError):
            subscription.sudo().write({'gueltig_von': fields.datetime.now()})

    def test_03_restrict_unlink_subscription_for_backend_users(self):
        """ Unlink subscription for group in restricted group folder as backend user and admin user """
        subscription = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        self.assertTrue(subscription.exists())
        # Backend User
        with self.assertRaises(AccessError):
            subscription.sudo(user=self.backend_user).unlink()
        # Admin User
        with self.assertRaises(AccessError):
            subscription.sudo().unlink()

    def test_04_allow_create_write_unlink_subscription_for_sosync_users(self):
        """ Create, write, unlink subscription for group in restricted group folder as sosync user """
        subscription = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        self.assertTrue(subscription.exists())
        subscription.write({'gueltig_von': fields.datetime.now()})
        subscription.unlink()
        self.assertFalse(subscription.exists())

    def test_05_restrict_multiple_assignments_for_groups_in_same_groupfolder(self):
        """ Restrict multiple group assignments for groups in a group folder with nur_eine_gruppe_anmelden = True """
        subscription_a = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        self.assertTrue(subscription_a.exists())
        self.assertTrue(self.group_newsletter_b.zgruppe_id.nur_eine_gruppe_anmelden)
        with self.assertRaises(ValidationError):
            subscription_b = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
                'zgruppedetail_id': self.group_newsletter_b.id,
                'frst_personemail_id': self.partner_max1.main_personemail_id.id,
            })

    def test_06_allow_multiple_assignments_for_groups_in_same_groupfolder(self):
        self.group_newsletter_b.zgruppe_id.nur_eine_gruppe_anmelden = False
        self.assertFalse(self.group_newsletter_b.zgruppe_id.nur_eine_gruppe_anmelden)
        subscription_a = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        self.assertTrue(subscription_a.exists())
        subscription_b = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter_b.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        self.assertTrue(subscription_b.exists())
