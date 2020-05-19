# -*- coding: utf-8 -*-

from openerp.tests import common
from openerp.exceptions import ValidationError
from openerp.tools.safe_eval import safe_eval

import logging
logger = logging.getLogger(__name__)


class TestFRSTPersonEmail(common.TransactionCase):
    def setUp(self):
        super(TestFRSTPersonEmail, self).setUp()

        self.main_comp = self.env.ref('base.main_company')
        self.user_group = self.env.ref('base.group_erp_manager')

        # Create User 1
        self.user_max1 = self.env['res.users'].sudo().create({
            'name': u"Max1 Mustermann",
            'login': u"max1@test.com",
            #'company_id': self.main_comp.id,
            #'groups_id': [(4, self.user_group.id)],
        })

        # Store Partner 1 for quick access
        self.partner_max1 = self.user_max1.partner_id

        # Create User 2
        self.user_max2 = self.env['res.users'].create({
            'name': u"Max2 Mustermann",
            'login': u"max2@test.com",
            'company_id': self.main_comp.id,
            'groups_id': [(4, self.user_group.id)],
        })

        # Store Partner 2 for quick access
        self.partner_max2 = self.user_max2.partner_id

    def test_10_merge_two_partner_with_two_users(self):
        """ Test the merging of two partners that are each linked to a res.user"""
        partner_obj = self.env['res.partner']
        partner_obj.fso_merge(remove_id=self.partner_max2.id,
                              keep_id=self.partner_max1.id)
        # Make sure the the user of the partner-to-remove was also merged and then removed!
        # TODO: Test that records that where linked to the user-to-remove where merged into the user-to-keep
        self.assertFalse(self.user_max2.exists())

    def test_11_merge_two_partner_user_for_partner_to_remove(self):
        """ Test the merging of two partners where only the partner-to-remove is linked to a res.user """
        partner_obj = self.env['res.partner']
        self.partner_to_keep = self.env['res.partner'].create({'name': 'partner-to-keep', 'email': 'partner@to.keep'})
        partner_obj.fso_merge(remove_id=self.partner_max2.id,
                              keep_id=self.partner_to_keep.id)
        # Make sure the res.user is now linked to the partner-to-keep
        self.assertTrue(self.user_max2.exists())
        self.assertEqual(self.user_max2.partner_id.id, self.partner_to_keep.id)

    def test_20_merge_partner_with_child_relation(self):
        """ Assert that partner-to-remove can not be merged if it is a child of the partner to keep! """
        partner_obj = self.env['res.partner']
        self.partner_max2.parent_id = self.partner_max1.id
        with self.assertRaises(ValidationError):
            partner_obj.fso_merge(remove_id=self.partner_max2.id,
                                  keep_id=self.partner_max1.id)

    def test_30_merge_partner_with_parent_relation(self):
        """ Assert that partner-to-remove can not be merged if it is a parent of the partner-to-keep! """
        partner_obj = self.env['res.partner']
        self.partner_max1.parent_id = self.partner_max2.id
        with self.assertRaises(ValidationError):
            partner_obj.fso_merge(remove_id=self.partner_max2.id,
                                  keep_id=self.partner_max1.id)

    # def test_02_classic_merge_partner_with_users(self):
    #     logger.info("TEST 02: MERGE res.partner (remove_id) %s OF PERSON MAX2 %s "
    #                 "INTO res.partner (keep_id) %s OF PERSON MAX1 %s AND res.user witch classic wizzard!"
    #                 "" % (self.partner_max2.id, self.partner_max2.id,
    #                       self.partner_max1.id, self.partner_max1.id))
    #     merge_wizard = self.env['base.partner.merge.automatic.wizard'].create({
    #         'state': 'selection',
    #         'partner_ids': [(6, False, [self.partner_max1.id, self.partner_max2.id])],
    #         'dst_partner_id': self.partner_max1.id
    #     })
    #     next_screen = merge_wizard.merge_cb()
    #     # Make sure the merged PersonEmail is not existing any more
    #     self.assertFalse(self.user_max2.exits())

