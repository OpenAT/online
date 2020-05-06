# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp.tools.safe_eval import safe_eval

import logging
logger = logging.getLogger(__name__)


class TestFRSTPersonEmail(common.TransactionCase):
    def setUp(self):
        super(TestFRSTPersonEmail, self).setUp()

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

        # Create a second local Group: group_urgentaction
        self.group_urgentaction = self.env['frst.zgruppedetail'].create({
            'zgruppe_id': self.groupfolder_email.id,
            'gruppe_kurz': 'Group Urgentaction',
            'gruppe_lang': 'Group Urgentaction',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
        })

        # Create a third local Group: group_acitivists
        self.group_acitivists = self.env['frst.zgruppedetail'].create({
            'zgruppe_id': self.groupfolder_email.id,
            'gruppe_kurz': 'Group Activists',
            'gruppe_lang': 'Group Activists',
            'gui_anzeigen': True,
            'geltungsbereich': 'local',
        })

        # Create Partner 1 with a PersonEmail
        self.partner_max1 = self.env['res.partner'].create({
            'name': u"Max1 Mustermann",
            'email': u"max@test.com"
        })
        # Assign group_newsletter to the PersonEmail of Partner 1
        self.subscription_max1_group_newsletter = self.env['frst.personemailgruppe'].create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })
        # Assign group_urgentaction to the PersonEmail of Partner 1
        self.subscription_max1_group_urgentaction = self.env['frst.personemailgruppe'].create({
            'zgruppedetail_id': self.group_urgentaction.id,
            'frst_personemail_id': self.partner_max1.main_personemail_id.id,
        })

        # Create Partner 2
        self.partner_max2 = self.env['res.partner'].create({
            'name': u"Max2 Mustermann",
            'email': u"max@test.com"
        })
        # Assign group_newsletter to the PersonEmail of Partner 2
        self.subscription_max2_group_newsletter = self.env['frst.personemailgruppe'].create({
            'zgruppedetail_id': self.group_newsletter.id,
            'frst_personemail_id': self.partner_max2.main_personemail_id.id,
        })
        # Assign group_acitivists to the PersonEmail of Partner 2
        self.subscription_max2_group_activists = self.env['frst.personemailgruppe'].create({
            'zgruppedetail_id': self.group_acitivists.id,
            'frst_personemail_id': self.partner_max2.main_personemail_id.id,
        })

    def test_01_merge_personemails_with_different_groups_of_two_different_partners(self):
        """ Test the merging of two PersonEmails-with-groups from different persons"""
        personemail_obj = self.env['frst.personemail']
        logger.info("TEST 04: MERGE PERSONEMAIL (remove_id) %s OF PERSON MAX2 %s "
                    "INTO PERSONEMAIL (keep_id) %s OF PERSON MAX1 %s"
                    "" % (self.partner_max2.main_personemail_id.id, self.partner_max2.id,
                          self.partner_max1.main_personemail_id.id, self.partner_max1.id))
        personemail_obj.fso_merge(remove_id=self.partner_max2.main_personemail_id.id,
                                  keep_id=self.partner_max1.main_personemail_id.id)
        # Make sure the merged PersonEmail is not existing any more
        self.assertFalse(self.partner_max2.main_personemail_id)
        self.assertFalse(self.partner_max2.frst_personemail_ids)
        # Check that the group-subscriptions where 'transfered' to the remaining PersonEmail of Partner 1
        self.assertEqual(self.subscription_max2_group_activists.frst_personemail_id.id,
                         self.partner_max1.main_personemail_id.id)
        self.assertEqual(self.subscription_max2_group_newsletter.frst_personemail_id.id,
                         self.partner_max1.main_personemail_id.id)
