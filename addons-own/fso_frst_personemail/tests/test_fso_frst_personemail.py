# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp.tools.safe_eval import safe_eval

import logging
logger = logging.getLogger(__name__)


class TestFRSTPersonEmail(common.TransactionCase):
    def setUp(self):
        super(TestFRSTPersonEmail, self).setUp()

        self.partner_max1 = self.env['res.partner'].create({
            'name': u"Max Mustermann",
            'email': u"max@test.com"
        })

        self.partner_max2 = self.env['res.partner'].create({
            'name': u"Max Mustermann",
            'email': u"max@test.com"
        })

    # ATTENTION: Tests have no specific order! Therefore i use the "dumb" method of numbers added!
    # ATTENTION: The setUp() is done individually for every test:
    #            !!! Tests do NOT share the data !!!

    def test_01_create_partner_and_main_personemail(self):
        self.assertEqual(self.partner_max1.email, u"max@test.com")
        self.assertEqual(self.partner_max1.main_personemail_id.email, self.partner_max1.email)

    def test_02_update_partner_email(self):
        """ Create a new PersonEmail which must be the new Hauptemailadresse """
        self.partner_max1.write({'email': 'max_email2@test.com'})
        self.assertEqual(self.partner_max1.email, 'max_email2@test.com')
        self.assertEqual(self.partner_max1.main_personemail_id.email, self.partner_max1.email)
        self.assertIs(len(self.partner_max1.frst_personemail_ids), 2)

    def test_03_reactivate_partner_email(self):
        """ Reactivate the first PersonEmail and set it as the Hauptemailadresse """
        self.partner_max1.write({'email': 'max_email2@test.com'})
        self.partner_max1.write({'email': 'max@test.com'})
        self.assertEqual(self.partner_max1.email, 'max@test.com')
        self.assertEqual(self.partner_max1.main_personemail_id.email, self.partner_max1.email)
        self.assertIs(len(self.partner_max1.frst_personemail_ids), 2)

    def test_04_merge_personemail(self):
        """ Test the merging of two PersonEmail from different persons """
        personemail_obj = self.env['frst.personemail']
        logger.info("TRY TO MERGE PERSONEMAIL (remove_id) %s OF PERSON MAX2 %s "
                    "INTO PERSONEMAIL (keep_id) %s OF PERSON MAX1 %s"
                    "" % (self.partner_max2.main_personemail_id.id, self.partner_max2.id,
                          self.partner_max1.main_personemail_id.id, self.partner_max1.id))
        personemail_obj.fso_merge(remove_id=self.partner_max2.main_personemail_id.id,
                                  keep_id=self.partner_max1.main_personemail_id.id)
        self.assertIsNone(self.partner_max2.main_personemail_id)
        self.assertIsNone(self.partner_max2.frst_personemail_ids)
