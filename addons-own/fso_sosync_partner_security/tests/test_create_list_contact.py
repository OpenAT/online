# -*- coding: utf-8 -*-
from openerp.tests import common


import logging
logger = logging.getLogger(__name__)


class TestResPartnerSecurityFields(common.TransactionCase):
    def setUp(self):
        super(TestResPartnerSecurityFields, self).setUp()

        # ATTENTION: It is necessary to clean the ir.model.data cache or fragments will remain between tests which
        #            would lead to wrong results for self.env.ref()
        @self.addCleanup
        def reset_model_data_cache():
            self.env.invalidate_all()
            self.env['ir.model.data'].clear_caches()
            self.env['res.groups'].clear_caches()

        self.user1 = self.env["res.users"].create({
            "name": "Test User",
            "login": "test_user@test.com",
        })
        self.partner1 = self.user1.partner_id

        # Since this addon only depends on base we have to create all the user groups if they do not exist
        special_group_xml_ids = ['fso_base.instance_system_user', 'base.studio', 'base.sosync']
        for g_xml_id in special_group_xml_ids:
            group = self.env.ref(g_xml_id, raise_if_not_found=False)
            if not group:
                group = self.env['res.groups'].create({
                    'name': 'Test group ' + g_xml_id,
                    'implied_ids': [
                        (4, self.env.ref('base.group_user').id),
                        (4, self.env.ref('base.group_no_one').id),
                    ]
                })
                # Create xml id:
                self.env['ir.model.data'].create({
                    'module': g_xml_id.split('.')[0],
                    'name': g_xml_id.split('.')[1],
                    'model': 'res.groups',
                    'res_id': group.id
                })
                self.env.ref(g_xml_id)

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
            group = self.env.ref(group_xml_id)
            if group:
                self.user1.write({"groups_id": [(4, group.id, "")]})
                self.assertTrue(self.partner1.fson_system_user)

        # Remove groups
        for group_xml_id in group_xml_ids:
            group = self.env.ref(group_xml_id)
            if group:
                self.user1.write({"groups_id": [(3, group.id, "")]})
                if self.user1.groups_id:
                    self.assertTrue(self.partner1.fson_system_user)
                else:
                    self.assertFalse(self.partner1.fson_system_user)
