# -*- coding: utf-8 -*-

from openerp import models, fields


class CrmLeadSosync(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'base.sosync']

    company_id = fields.Many2one(sosync="True")
    partner_id = fields.Many2one(sosync="True")
    partner_name = fields.Char(sosync="True")

    name = fields.Char(sosync="True")
    contact_name = fields.Char(sosync="True")
    contact_lastname = fields.Char(sosync="True")
    contact_anrede_individuell = fields.Char(sosync="True")
    contact_birthdate_web = fields.Date(sosync="True")
    contact_newsletter_web = fields.Boolean(sosync="True")
    contact_title_web = fields.Char(sosync="True")
    title = fields.Many2one(sosync="True")
    title_action = fields.Char(sosync="True")
    function = fields.Char(sosync="True")

    email_from = fields.Char(sosync="True")
    phone = fields.Char(sosync="True")
    mobile = fields.Char(sosync="True")
    fax = fields.Char(sosync="True")

    country_id = fields.Many2one(sosync="True")
    state_id = fields.Many2one(sosync="True")
    zip = fields.Char(sosync="True")
    city = fields.Char(sosync="True")
    street = fields.Char(sosync="True")
    street2 = fields.Char(sosync="True")
    contact_street_number_web = fields.Char(sosync="True")

    description = fields.Text(sosync="True")

    date_action = fields.Date(sosync="True")
    date_action_last = fields.Datetime(sosync="True")
    date_action_next = fields.Datetime(sosync="True")
    date_assign = fields.Date(sosync="True")
    date_closed = fields.Datetime(sosync="True")
    date_deadline = fields.Date(sosync="True")
    date_last_stage_update = fields.Datetime(sosync="True")
    date_open = fields.Datetime(sosync="True")
    day_close = fields.Float(sosync="True")
    day_open = fields.Float(sosync="True")
    opt_out = fields.Boolean(sosync="True")

    partner_address_email = fields.Char(sosync="True")
    partner_address_name = fields.Char(sosync="True")
    payment_mode = fields.Many2one(sosync="True")

    type = fields.Selection(sosync="True")
