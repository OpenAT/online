# -*- coding: utf-8 -*-
from openerp.tests import common
from datetime import datetime
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

        # Create a CDS entry
        self.cds_record = self.env['frst.zverzeichnis'].create({
            "verzeichnisname": "Test Facebook CDS Record",
            "verzeichnistyp_id": False,
            "bezeichnungstyp_id": "KA",
        })

        # Create a facebook page
        self.fb_page = self.env['crm.facebook.page'].create({
            "name": "Test Facebook Page",
            "fb_page_id": "1234",
            "fb_page_access_token": "4321",
        })

        # Create a facebook (leads) form for a phone petition
        self.fb_form = self.env['crm.facebook.form'].create({
            "name": "Test Facebook Form",
            "active": True,
            "activated": datetime.now(),
            "state": 'active',
            "fb_form_id": "5678",
            "crm_page_id": self.fb_page.id,
            # HINT: The crm.lead fields will be auto mapped based on the fb_field_type by
            #       facebook_field_type_to_odoo_field_name()
            # HINT: (0, _, values) -> adds a new record created from the provided value dict.
            "mappings": [
                # FULL_NAME -> contact_name
                (0, "", {"fb_field_id": "1", "fb_field_key": "full_name", "fb_field_type": "FULL_NAME"}),
                # PHONE -> phone
                (0, "", {"fb_field_id": "2", "fb_field_key": "phone_number", "fb_field_type": "PHONE"}),
            ],
            # fso_crm_facebook_leads
            "force_create_partner": True,
            "frst_import_type": "phone",
            "frst_zverzeichnis_id": self.cds_record.id,
        })

    def test_01_create_phone_petition_lead_link_existing_partner(self):
        facebook_lead_data = {
            'id': '987654321',
            'field_data': [
                {'name': 'full_name', 'values': ['Max Mustermann']},
                {'name': 'phone_number', 'values': ['+43 3172 1234567']},
            ]
        }
        crm_lead_data = self.fb_form.facebook_data_to_lead_data(facebook_lead_data=facebook_lead_data)
        lead = self.env['crm.lead'].create(crm_lead_data)
        self.assertTrue(lead.contact_name == 'Max Mustermann')
        self.assertTrue(lead.partner_id.id == self.partner.id)
        self.assertTrue(lead.partner_id.name == 'Test User')

    def test_02_create_phone_petition_lead_create_partner_none_found(self):
        facebook_lead_data = {
            'id': '987654322',
            'field_data': [
                {'name': 'full_name', 'values': ['Max Mustermann']},
                {'name': 'phone_number', 'values': ['+43 664 987654321']},
            ]
        }
        crm_lead_data = self.fb_form.facebook_data_to_lead_data(facebook_lead_data=facebook_lead_data)
        lead = self.env['crm.lead'].create(crm_lead_data)
        self.assertTrue(lead.contact_name == 'Max Mustermann')
        self.assertTrue(lead.partner_id.name == 'Max Mustermann')

    def test_03_create_phone_petition_lead_create_partner_two_found(self):
        # Create partner2 with the same phone number as partner
        self.partner2 = self.env["res.partner"].create({
            "name": "Test User 2",
            "phone": self.partner.phone,
        })
        facebook_lead_data = {
            'id': '987654322',
            'field_data': [
                {'name': 'full_name', 'values': ['Max Mustermann']},
                {'name': 'phone_number', 'values': [self.partner.phone]},
            ]
        }
        crm_lead_data = self.fb_form.facebook_data_to_lead_data(facebook_lead_data=facebook_lead_data)
        lead = self.env['crm.lead'].create(crm_lead_data)
        self.assertTrue(lead.contact_name == 'Max Mustermann')
        self.assertTrue(lead.partner_id.name == 'Max Mustermann')
