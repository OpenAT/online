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

        # Create a partner with a phone number
        self.partner = self.env["res.partner"].create({
            "name": "Test User",
            "phone": " 0043 03172 12-34-56-7 ",
            "mobile": " 0043 (0) 660 12-34-56-7 ",
        })

    def test_01_find_phone_single_match(self):
        partner_obj = self.env['res.partner']
        found = partner_obj.search_phone_fuzzy('+43 3172 123 456 7')
        self.assertTrue(len(found) == 1)

    def test_02_find_mobile_single_match(self):
        partner_obj = self.env['res.partner']
        found = partner_obj.search_phone_fuzzy('+43 660_12__34-56--(7)')
        self.assertTrue(len(found) == 1)

    def test_03_find_phone_single_match_multiple_zeros(self):
        partner_obj = self.env['res.partner']
        found = partner_obj.search_phone_fuzzy('00043 (0) 3172 123 456 7')
        self.assertTrue(len(found) == 1)

    def test_04_find_phone_single_match_multiple_plus(self):
        partner_obj = self.env['res.partner']
        found = partner_obj.search_phone_fuzzy('++43 (0) 3172+123++456+7+')
        self.assertTrue(len(found) == 1)

    def test_05_find_phone_and_mobile_single_match(self):
        self.partner.phone = self.partner.mobile
        partner_obj = self.env['res.partner']
        found = partner_obj.search_phone_fuzzy('  0043 0 660 1234567  ')
        self.assertTrue(len(found) == 1)
        for record, values in found.iteritems():
            self.assertTrue(all(field in values.keys() for field in ['phone', 'mobile']))

    def test_06_find_phone_multi_match(self):
        self.partner2 = self.env["res.partner"].create({
            "name": "Test User 2",
            "mobile": "  ++43 (0) 660 1234 567 ",
        })
        partner_obj = self.env['res.partner']
        found = partner_obj.search_phone_fuzzy('  +43 660 1234567  ')
        self.assertTrue(len(found) == 2)

    def test_07_find_phone_no_country_no_match(self):
        partner_obj = self.env['res.partner']
        found = partner_obj.search_phone_fuzzy('03172 1234567')
        self.assertTrue(len(found) == 0)

    def test_08_find_phone_no_country_in_both_match(self):
        partner_obj = self.env['res.partner']
        self.partner.phone = '03172 1234567'
        found = partner_obj.search_phone_fuzzy('(0) 3172 123-456-7')
        self.assertTrue(len(found) == 1)
