# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import ValidationError

from datetime import datetime
from datetime import timedelta

import logging
logger = logging.getLogger(__name__)


class TestFRSTPersonEmailGruppe(common.TransactionCase):
    def setUp(self):
        super(TestFRSTPersonEmailGruppe, self).setUp()

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

    def test_01_inactivate_personemail_inactivates_personemailgruppe(self):
        self.assertIn(self.subscription_max1_group_newsletter.state, ['subscribed', 'approved'])
        self.assertIn(self.subscription_max1_group_urgentaction.state, ['subscribed', 'approved'])
        email_max = self.partner_max1.main_personemail_id
        self.assertTrue(email_max.state == 'active')
        email_max.write({'gueltig_bis': datetime.now() - timedelta(days=1)})
        self.assertTrue(email_max.state == 'inactive')
        self.assertNotIn(self.subscription_max1_group_newsletter.state, ['subscribed', 'approved'])
        self.assertNotIn(self.subscription_max1_group_urgentaction.state, ['subscribed', 'approved'])

    def test_02_inactivate_personemail_reactivate_personemailgruppe_assertion(self):
        email_max = self.partner_max1.main_personemail_id
        self.assertTrue(email_max.state == 'active')
        self.assertIn(self.subscription_max1_group_newsletter.state, ['subscribed', 'approved'])
        # Inactivate the E-Mail which to inactivate all related personemailgruppe(n)
        email_max.write({'gueltig_bis': datetime.now() - timedelta(days=1)})
        self.assertTrue(email_max.state == 'inactive')
        self.assertNotIn(self.subscription_max1_group_newsletter.state, ['subscribed', 'approved'])
        # Try to reactivate a personeamilgruppe for the inactive email
        with self.assertRaises(ValidationError):
            self.subscription_max1_group_newsletter.write({'gueltig_bis': datetime.now() + timedelta(days=1)})
