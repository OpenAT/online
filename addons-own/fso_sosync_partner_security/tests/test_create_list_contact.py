# -*- coding: utf-8 -*-
from openerp.tests import common


import logging
logger = logging.getLogger(__name__)


class TestResPartnerSecurityFields(common.TransactionCase):
    def setUp(self):
        super(TestResPartnerSecurityFields, self).setUp()

        self.user1 = self.env["res.users"].create({
            "name": "Test User",
            "login": "test_user@test.com",
        })
        self.partner1 = self.user1.partner_id

    def test_01_fson_donor_user(self):
        group_xml_id = "base.group_public"
        # Assign group
        self.user1.write({"groups_id": [(6, "", [self.env.ref(group_xml_id).id])]})
        self.assertTrue(len(self.user1.groups_id) == 1)
        self.assertTrue(self.user1.has_group(group_xml_id))
        self.assertTrue(self.partner1.fson_donor_user)
        # Remove all groups
        self.user1.write({"groups_id": [(5, "", "")]})
        self.assertFalse(self.user1.groups_id)
        self.assertFalse(self.partner1.fson_donor_user)

    def test_02_fson_system_user(self):
        group_xml_ids = ['base.group_no_one', 'fso_base.instance_system_user', 'base.studio', 'base.sosync']
        self.user1.write({"groups_id": [(5, "", "")]})
        self.assertFalse(self.user1.groups_id)
        self.assertFalse(self.partner1.fson_system_user)

        # Add groups
        for group_xml_id in group_xml_ids:
            self.user1.write({"groups_id": [(4, self.env.ref(group_xml_id).id, "")]})
            self.assertTrue(self.partner1.fson_system_user)

        # Remove groups
        for group_xml_id in group_xml_ids:
            self.user1.write({"groups_id": [(3, self.env.ref(group_xml_id).id, "")]})
            if self.user1.groups_id:
                self.assertTrue(self.partner1.fson_system_user)
            else:
                self.assertFalse(self.partner1.fson_system_user)
