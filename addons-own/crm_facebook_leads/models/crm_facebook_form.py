# -*- coding: utf-8 -*-

import openerp
from openerp import api, models, fields
import requests
from static_data import facebook_graph_api_url
try:
    import dateutil
    from dateutil.parser import parse
except:
    dateutil = False

import logging
logger = logging.getLogger(__name__)


class CrmFacebookForm(models.Model):
    _name = 'crm.facebook.form'
    _inherit = ['mail.thread']

    name = fields.Char(required=True, readonly=True)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection(selection=[('to_review', 'To review'),
                                        ('active', 'Active'),
                                        ('error', 'Error'),
                                        ('archived', 'Archived')],
                             string='State', index=True, track_visibility='onchange',
                             compute='compute_state', store=True, readonly=True)
    activated = fields.Datetime(string='Approved/Activated at', readonly=True, track_visibility='onchange')

    fb_form_id = fields.Char(string='Facebook Form ID', required=True, readonly=True)
    fb_form_locale = fields.Char(string="Facebook Form Locale", readonly=True)
    fb_form_status = fields.Char(string="Facebook Form Status", readonly=True)

    crm_page_id = fields.Many2one(string='Facebook Page',
                                  comodel_name='crm.facebook.page', inverse_name='crm_form_ids',
                                  index=True,
                                  required=True, readonly=True)
    mappings = fields.One2many(string="Form Field Mapping",
                               comodel_name='crm.facebook.form.field', inverse_name='crm_form_id',
                               track_visibility='onchange')

    # Sales team / leads section
    section_id = fields.Many2one(comodel_name='crm.case.section',
                                 index=True,
                                 domain=['|',
                                         ('use_leads', '=', True),
                                         ('use_opportunities', '=', True)],
                                 string="Sales Team")

    # UTM tracking
    campaign_id = fields.Many2one(comodel_name='utm.campaign', string='Campaign', index=True)
    source_id = fields.Many2one(comodel_name='utm.source', string='Source', index=True)
    medium_id = fields.Many2one(comodel_name='utm.medium', string='Medium', index=True)

    # Created crm.leads
    crm_lead_ids = fields.One2many(comodel_name='crm.lead', inverse_name='crm_form_id', readonly=True)
    crm_lead_ids_count = fields.Integer(string="Lead Count", compute="cmp_crm_lead_ids_count")

    # SQL CONSTRAINTS
    _sql_constraints = [
        ('fb_form_id_unique', 'unique(fb_form_id)', 'Facebook Form ID must be unique per form')
    ]

    # HINT: If the fb_page_access_token field is changed this method is triggered also!
    @api.depends('active', 'activated', 'crm_page_id', 'fb_form_id')
    def compute_state(self):
        for r in self:
            if not r.active:
                r.state = 'archived'
            elif not r.fb_form_id or not r.crm_page_id or not r.crm_page_id.fb_page_access_token:
                r.state = 'error'
            elif r.activated:
                r.state = 'active'
            else:
                r.state = 'to_review'

    @api.multi
    def cmp_crm_lead_ids_count(self):
        for r in self:
            r.crm_lead_ids_count = len(r.crm_lead_ids)

    @api.multi
    def button_activate(self):
        self.write({'activated': fields.datetime.now()})

    @api.multi
    def button_deactivate(self):
        self.write({'activated': False})

    @api.multi
    def button_archive(self):
        self.write({'active': False})

    @api.multi
    def button_unarchive(self):
        self.write({'active': True, 'activated': False})

    @api.multi
    def button_open_lead_graph(self):
        assert self.ensure_one(), "Please select one form only!"

        graph_view_id = self.env.ref('crm_facebook_leads.crm_case_graph_view_leads_facebook_form').id
        tree_view_id = self.env.ref('crm_facebook_leads.crm_lead_tree_view_facebook').id
        form_view_id = self.env.ref('crm.crm_case_form_view_oppor').id

        return {
            'domain': [('crm_form_id', '=', self.id)],
            'name': 'Facebook Leads for Form: "%s"' % self.name,
            'view_type': 'form',
            'view_mode': 'graph,tree,form',
            'res_model': 'crm.lead',
            'view_id': False,
            'views': [(graph_view_id, 'graph'), (tree_view_id, 'tree'), (form_view_id, 'form')],
            'context': "{}",
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def import_facebook_lead_fields(self):
        self.mappings.unlink()
        r = requests.get(facebook_graph_api_url + self.fb_form_id,
                         params={'access_token': self.crm_page_id.fb_page_access_token,
                                 'fields': 'questions,legal_content'}).json()

        # Regular questions
        # -----------------
        if r.get('questions'):
            for question in r.get('questions'):
                self.env['crm.facebook.form.field'].create({
                    'crm_form_id': self.id,
                    'fb_label': question['label'],
                    'fb_field_id': question['id'],
                    'fb_field_key': question['key'],
                    'fb_field_type': question.get('type', False)
                })

        # Disclaimer/Consent checkboxes
        # -----------------------------
        # HINT: This is sometimes abused by the customers for newsletter signup
        if r.get('legal_content') and r['legal_content'].get('custom_disclaimer'):
            for checkbox in r['legal_content']['custom_disclaimer'].get('checkboxes', []):
                self.env['crm.facebook.form.field'].create({
                    'crm_form_id': self.id,
                    'fb_label': checkbox['text'],
                    'fb_field_id': checkbox['id'],
                    'fb_field_key': checkbox['key'],
                    'fb_field_type': "CONSENT_CHECKBOX"
                })

    # TODO: We Could add the facebook form locale information to this process!
    @staticmethod
    def parse_date(string_val, date_type=None):
        assert date_type in ('date', 'datetime'), "type must be 'date' or 'datetime'"

        if not dateutil:
            logger.error("Facebook Leads Import: dateutil library is not available!")
            return False

        try:
            parsed_dt = parse(string_val)
            if date_type == 'date':
                parsed_dt = parsed_dt.date()
            return parsed_dt
        except Exception as e:
            logger.error("Facebook Leads Import: Could not convert string %s to datetime!\n%s"
                         "" % (string_val, repr(e)))
            return False

    @api.multi
    def facebook_data_to_lead_data(self, facebook_lead_data=None):
        assert isinstance(facebook_lead_data, dict), "facebook_lead_data must be a dictionary!"
        self.ensure_one()
        crm_form = self

        # Basic crm.lead data
        date_open = fields.datetime.now()
        if facebook_lead_data.get('created_time'):
            try:
                date_open = facebook_lead_data['created_time'].split('+')[0].replace('T', ' ')
            except Exception as e:
                logger.error("Could not convert facebook lead create time! %s" % repr(e))
        vals = {
            'fb_lead_id': facebook_lead_data['id'],
            'date_open': date_open,
            'description': '',
            'section_id': crm_form.section_id and crm_form.section_id.id,
            'campaign_id': crm_form.campaign_id and crm_form.campaign_id.id,
            'source_id': crm_form.source_id and crm_form.source_id.id,
            'medium_id': crm_form.medium_id and crm_form.medium_id.id,
            'crm_page_id': crm_form.crm_page_id.id,
            'crm_form_id': crm_form.id,
        }

        # Loop through the question answers
        # ---------------------------------
        # TODO: Currently we only support facebook questions with a single answer/value
        for question in facebook_lead_data['field_data']:
            question_fb_field_key = question.get('name')
            question_val = question['values'][0]

            # Check if the facebook field is mapped to a crm.lead field
            crm_facebook_form_field = crm_form.mappings.filtered(lambda f: f.fb_field_key == question_fb_field_key)

            # Try to convert question data to valid odoo field data for mapped fields
            odoo_field_name = False
            odoo_field_value = False
            if crm_facebook_form_field:

                odoo_field = crm_facebook_form_field.crm_field
                odoo_field_name = odoo_field.name
                odoo_field_type = odoo_field.ttype

                try:
                    # Many2One
                    if odoo_field_type == 'many2one':
                        domain = [('name', '=', question_val)]
                        if odoo_field.relation == 'res.country':
                            domain = [('code', '=', question_val)]
                        rec = self.env[odoo_field.relation].search(domain, limit=1)
                        odoo_field_value = rec.id if rec else False
                    # Float
                    elif odoo_field_type in ('float', 'monetary'):
                        odoo_field_value = float(question_val)
                    # Int
                    elif odoo_field_type == 'integer':
                        odoo_field_value = int(question_val)
                    # Date
                    elif odoo_field_type in ('date', 'datetime'):
                        # TODO: We could add the facebook form locale information to the parsing method!
                        odoo_field_value = CrmFacebookForm.parse_date(question_val, date_type=odoo_field_type)
                    # Selection
                    elif odoo_field_type == 'selection':
                        # TODO: Check if question_val is a valid selection value! If not add it to the comments!
                        odoo_field_value = question_val
                    # Char
                    elif odoo_field_type in ('char', 'text'):
                        odoo_field_value = question_val
                except Exception as e:
                    logger.error("Could not convert facebook question data to valid odoo field data! %s" % repr(e))

            # Add the data to the values
            if odoo_field_name and odoo_field_value:
                vals.update({odoo_field_name: odoo_field_value})
            else:
                # ATTENTION: This is porcelain and is expected by other addons - do not change the structure!
                vals['description'] += question_fb_field_key + ': ' + question_val + '\n'

        # Use Email for 'contact_lastname' if the fields 'contact_name' and 'contact_lastname' and 'partner_name' are
        # not mapped!
        if not crm_form.mappings.filtered(lambda f: f.crm_field.name in ('contact_name', 'contact_lastname')):
            logger.warning("No fields are mapped for the partner name! Trying to use the e-mail as the partner name!")
            if vals.get('email_from') and 'contact_name' not in vals and 'contact_lastname' not in vals:
                vals['contact_name'] = vals.get('email_from')
                logger.warning("Using 'email_from' for 'contact_name'! final record vals: %s" % vals)

        # Always add the name field for the crm.lead
        if not vals.get('name'):
            if vals.get('partner_name'):
                vals['name'] = vals.get('partner_name')
            elif vals.get('firstname') or vals.get('lastname'):
                vals['name'] = (vals['firstname'] + ' ') if vals.get('firstname') else '' + vals.get('lastname', '')
            else:
                vals['name'] = 'facebook_lead_' + vals['fb_lead_id']

        # Loop through the disclaimer answers
        # -----------------------------------
        for checkbox in facebook_lead_data.get('custom_disclaimer_responses', []):
            checkbox_fb_field_key = checkbox.get('checkbox_key')
            checkbox_val = True if checkbox['is_checked'] == "1" else False

            # Check if the facebook field is mapped to a crm.lead field
            crm_facebook_form_field = crm_form.mappings.filtered(lambda f: f.fb_field_key == checkbox_fb_field_key)

            if crm_facebook_form_field and crm_facebook_form_field.crm_field:
                odoo_field = crm_facebook_form_field.crm_field
                odoo_field_name = odoo_field.name
                odoo_field_type = odoo_field.ttype
                assert odoo_field_type == 'boolean', "Disclaimer checkbox must be mapped to a boolean field!"
                vals.update({odoo_field_name: checkbox_val})
            else:
                # ATTENTION: This is porcelain and is expected by other addons - do not change the structure!
                vals['description'] += checkbox_fb_field_key + ': ' + str(checkbox_val) + '\n'

        # Return the values
        # -----------------
        return vals

    @api.multi
    def import_facebook_paginated_leads(self, crm_form, leads, imported_fb_lead_ids, raise_exception=True):
        logger.info('Got %s paginated leads from facebook for form %s' % (len(leads), crm_form.id))

        # Only import new leads
        new_leads = [ld for ld in leads if ld['id'] not in imported_fb_lead_ids]
        logger.info('Importing %s new paginated leads from facebook for form %s' % (len(new_leads), crm_form.id))

        # Convert the facebook lead data to crm.leads records
        for lead in new_leads:

            # Create a new environment to avoid side effects if lead creation fails and no exception should be raised
            if not raise_exception:
                # You don't need clear caches because they are cleared when the "with" finishes
                with openerp.api.Environment.manage():
                    # This will close your cr when the "with" finishes
                    with openerp.registry(self.env.cr.dbname).cursor() as new_cr:
                        new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                        try:
                            new_form = crm_form.with_env(new_env)
                            crm_lead_values = new_form.facebook_data_to_lead_data(lead)
                            crm_lead = new_form.env['crm.lead'].create(crm_lead_values)
                            logger.info("Lead with id %s was successfully created!" % crm_lead.id)
                        except Exception as e:
                            logger.error("Could not import lead %s because of %s!" % (lead, repr(e)))
                            logger.warning("Exception is suppress! Rollback cursor and continue with next lead!")
                            if new_form.env.cr is not None:
                                new_form.env.cr.rollback()
                            pass
            else:
                crm_lead_values = crm_form.facebook_data_to_lead_data(lead)
                crm_lead = self.env['crm.lead'].create(crm_lead_values)
                logger.info("Lead with id %s was successfully created!" % crm_lead.id)

    @api.multi
    def import_facebook_leads(self, raise_exception=True):
        # Get all active forms if no specific forms are selected
        if not self:
            crm_forms_active = self.env['crm.facebook.form'].search([('state', '=', 'active')])
        else:
            crm_forms_active = self.filtered(lambda frm: frm.state == 'active')
        logger.info("Import facebook leads for %s active forms" % len(crm_forms_active))

        for crm_form in crm_forms_active:
            # List of facebook lead ids of already imported leads
            imported_fb_lead_ids = crm_form.crm_lead_ids.mapped('fb_lead_id')

            # Get leads data from facebook for this form
            fb_request_url = facebook_graph_api_url + crm_form.fb_form_id + "/leads" + \
                             "?fields=created_time,field_data,custom_disclaimer_responses"
            logger.info("Import facebook leads from request url: %s" % fb_request_url)
            answer = requests.get(fb_request_url,
                                  params={'access_token': crm_form.crm_page_id.fb_page_access_token}).json()

            if not answer.get('data'):
                logger.warning("Received no leads data for form with ID %s" % crm_form.id)
                continue

            while answer.get('data'):
                self.import_facebook_paginated_leads(crm_form=crm_form,
                                                     leads=answer['data'],
                                                     imported_fb_lead_ids=imported_fb_lead_ids,
                                                     raise_exception=raise_exception)

                # Request next page, if there is one, otherwise break the loop
                paging = answer['paging']
                if paging.get('next'):
                    answer = requests.get(paging['next']).json()
                else:
                    break

    @api.model
    def scheduled_import_facebook_leads(self):
        self.import_facebook_leads(raise_exception=False)
