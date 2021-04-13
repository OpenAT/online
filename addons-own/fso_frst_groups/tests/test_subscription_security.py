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

        def reset():
            super(TestFRSTSubscriptionSecurity, self).reset()
            self.env.invalidate_all()
            self.env['ir.model.data'].clear_caches()
            self.env['res.groups'].clear_caches()

        # Create local GroupFolder
        self.groupfolder_email = self.env['frst.zgruppe'].create({
            'tabellentyp_id': '100110',
            'gruppe_kurz': 'Gruppenordner email',
            'gruppe_lang': 'Gruppenordner email',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
            # ATTENTION: This addon does not depend on the fso_base. Therefore the usergroup base.sosync may not
            #            exist when these test run. To overcome this problem we create the group folder with
            #            'gui_gruppen_bearbeiten_moeglich = True' and only after we created the subscription switch
            #            this to gui_gruppen_bearbeiten_moeglich = False'
            'gui_gruppen_bearbeiten_moeglich': True,
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
        group_frst_group_manager_id = self.ref("fso_frst_groups.group_fs_group_manager")
        self.backend_user = self.env['res.users'].create({
            'login': u'backend_test_user_djkiueukja883hkasdasdfe@test.com',
            'name': u'Backend Test User',
            "groups_id": [(6, 0, [group_frst_group_manager_id])]
        })

        # Create a subscription
        # TODO: If there are no subscriptions this will create !!!TWO!! subscriptions !!! DEBUG THIS!
        self.subscription = self.env['frst.personemailgruppe'].sudo().create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })

        # Create a sosync user
        group_sosync = self.env.ref('base.sosync', raise_if_not_found=False)
        if not group_sosync:
            #self.env.invalidate_all()
            self.env['ir.model.data'].clear_caches()
            self.env['res.groups'].clear_caches()
            group_sosync = self.env['res.groups'].create({
                'name': 'Sosync User Group for unit tests',
                'implied_ids': [
                   (4, self.env.ref('base.group_user').id),
                   (4, self.env.ref('base.group_no_one').id),
                   (4, self.env.ref('fso_frst_groups.group_fs_group_manager').id),
                   ]
            })
            # Create xml id:
            self.env.invalidate_all()
            xml_id = self.env['ir.model.data'].create({
                'module': 'base',
                'name': 'sosync',
                'model': 'res.groups',
                'res_id': group_sosync.id
            })
        group_sosync_id = self.env.ref("base.sosync").id
        self.sosync_user = self.env['res.users'].create({
            'login': u'sosync_test_user_djkfsodf3hkasdasdfe@test.com',
            'name': u'Sosync Test User',
            "groups_id": [(6, 0, [group_sosync_id])]
        })
        assert self.sosync_user.exists(), "Could not create sosync_user"

    def test_01_restrict_create_subscription_for_backend_users(self):
        """ Create subscription for group in restricted group folder as backend user and admin user """
        self.groupfolder_email.gui_gruppen_bearbeiten_moeglich = False
        self.assertFalse(self.groupfolder_email.gui_gruppen_bearbeiten_moeglich)
        with self.assertRaises(AccessError):
            new_subscription = self.env['frst.personemailgruppe'].sudo(user=self.backend_user).create({
                'zgruppedetail_id': self.group_newsletter.id,
                'frst_personemail_id': self.partner_max1.main_personemail_id.id,
            })
        with self.assertRaises(AccessError):
            new_subscription = self.env['frst.personemailgruppe'].sudo().create({
                'zgruppedetail_id': self.group_newsletter.id,
                'frst_personemail_id': self.partner_max1.main_personemail_id.id,
            })

    def test_02_restrict_write_subscription_for_backend_users(self):
        """ Write subscription for group in restricted group folder as backend user and admin user """
        self.assertTrue(self.subscription.exists())
        # Restrict editing to the base.sosync user group
        self.groupfolder_email.gui_gruppen_bearbeiten_moeglich = False
        self.assertFalse(self.groupfolder_email.gui_gruppen_bearbeiten_moeglich)
        # Backend User
        with self.assertRaises(AccessError):
            self.subscription.sudo(user=self.backend_user).write({'gueltig_von': fields.datetime.now()})
        # Admin User
        with self.assertRaises(AccessError):
            self.subscription.sudo().write({'gueltig_von': fields.datetime.now()})

    def test_03_restrict_unlink_subscription_for_backend_users(self):
        """ Unlink subscription for group in restricted group folder as backend user and admin user """
        self.assertTrue(self.subscription.exists())
        # Restrict editing to the base.sosync user group
        self.groupfolder_email.gui_gruppen_bearbeiten_moeglich = False
        self.assertFalse(self.groupfolder_email.gui_gruppen_bearbeiten_moeglich)
        # Backend User
        with self.assertRaises(AccessError):
            self.subscription.sudo(user=self.backend_user).unlink()
        # Admin User
        with self.assertRaises(AccessError):
            self.subscription.sudo().unlink()

    def test_04_allow_create_write_unlink_subscription_for_sosync_users(self):
        """ Create, write, unlink subscription for group in restricted group folder as sosync user """
        self.groupfolder_email.nur_eine_gruppe_anmelden = False
        self.assertFalse(self.groupfolder_email.nur_eine_gruppe_anmelden)
        subscription = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        self.assertTrue(subscription.exists())
        subscription.write({'gueltig_von': fields.datetime.now()})
        subscription.unlink()
        self.assertFalse(subscription.exists())

    def test_05_restrict_multiple_active_subscriptions_for_groups_in_same_groupfolder(self):
        """ Restrict multiple active group assignments for groups in a group folder with
            nur_eine_gruppe_anmelden = True
        """
        self.assertTrue(self.group_newsletter_b.zgruppe_id.nur_eine_gruppe_anmelden)
        # Create an active subscription (which should fail)
        # TODO: ATTENTION: This will create the subscription - i guess because the exception is suppressed ...
        #                  !!! Therefore i need to write smaller tests with only one with self.assertRaises ... !!!
        with self.assertRaises(ValidationError):
            subscription_b = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
                'zgruppedetail_id': self.group_newsletter_b.id,
                'frst_personemail_id': self.partner_max1.main_personemail_id.id,
            })
        # Create an inactive subscription (which should work)
        # TODO: This fails! Debug this!
        yesterday = fields.datetime.now() - timedelta(days=1)
        subscription_b_inactive = self.env['frst.personemailgruppe'].sudo(user=self.sosync_user).create({
            'zgruppedetail_id': self.group_newsletter_b.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
            'gueltig_von': yesterday,
            'gueltig_bis': yesterday
        })
        # Activate the inactive subscription (which should fail)
        with self.assertRaises(ValidationError):
            subscription_b_inactive.activate()

    def test_06_allow_multiple_subscriptions_for_groups_in_same_groupfolder(self):
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
