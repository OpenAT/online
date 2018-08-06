# -*- coding: utf-'8' "-*-"

from openerp import api, models, fields
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

import urllib


class MassMailingCampaign(models.Model):
    _inherit = "mail.mass_mailing.campaign"

    _inherits = {'utm.campaign': 'campaign_id'}
    _rec_name = "campaign_id"

    campaign_id = fields.Many2one('utm.campaign', 'campaign_id',
                                  required=True, ondelete='cascade',
                                  help="This name helps you tracking your different campaign efforts, "
                                       "e.g. Fall_Drive, Christmas_Special")
    source_id = fields.Many2one('utm.source', string='Source',
                                help="This is the link source, e.g. Search Engine, another domain,or name of email list",
                                default=lambda self: self.env.ref('utm.utm_source_newsletter'))
    medium_id = fields.Many2one('utm.medium', string='Medium',
                                help="This is the delivery method, e.g. Postcard, Email, or Banner Ad",
                                default=lambda self: self.env.ref('utm.utm_medium_email'))

    clicks_ratio = fields.Integer(compute="_compute_clicks_ratio", string="Number of clicks")

    # ---------------
    # COMPUTED FIELDS
    # ---------------
    def _compute_clicks_ratio(self):
        self.env.cr.execute("""
            SELECT COUNT(DISTINCT(stats.id)) AS nb_mails, COUNT(DISTINCT(clicks.mail_stat_id)) AS nb_clicks, stats.mass_mailing_campaign_id AS id
            FROM mail_mail_statistics AS stats
            LEFT OUTER JOIN link_tracker_click AS clicks ON clicks.mail_stat_id = stats.id
            WHERE stats.mass_mailing_campaign_id IN %s
            GROUP BY stats.mass_mailing_campaign_id
        """, (tuple(self.ids), ))

        campaign_data = self.env.cr.dictfetchall()
        mapped_data = dict([(c['id'], 100 * c['nb_clicks'] / c['nb_mails']) for c in campaign_data])
        for campaign in self:
            campaign.clicks_ratio = mapped_data.get(campaign.id, 0)


class MassMailing(models.Model):
    _inherit = "mail.mass_mailing"

    _inherits = {'utm.source': 'source_id'}
    _rec_name = "source_id"

    # FS-Online E-Mail Template
    # ATTENTION: With the added unique() sql constraint this is roughly a one2one field!
    email_template_id = fields.Many2one(string="FSO E-Mail Template",
                                        comodel_name="email.template", inverse_name="mass_mailing_ids",
                                        domain="[('fso_email_template','=',True)]",
                                        context="{'default_fso_email_template': True,}")

    # utm and link_tracker integration
    campaign_id = fields.Many2one('utm.campaign', string='Campaign',
                                  help="This name helps you tracking your different campaign efforts, e.g. Fall_Drive, Christmas_Special")
    source_id = fields.Many2one('utm.source', string='Subject', required=True, ondelete='cascade',
                                help="This is the link source, e.g. Search Engine, another domain, or name of email list")
    medium_id = fields.Many2one('utm.medium', string='Medium',
                                help="This is the delivery method, e.g. Postcard, Email, or Banner Ad", default=lambda self: self.env.ref('utm.utm_medium_email'))
    clicks_ratio = fields.Integer(compute="_compute_clicks_ratio", string="Number of Clicks")

    # ---------------
    # COMPUTED FIELDS
    # ---------------
    def _compute_clicks_ratio(self):
        self.env.cr.execute("""
            SELECT COUNT(DISTINCT(stats.id)) AS nb_mails, COUNT(DISTINCT(clicks.mail_stat_id)) AS nb_clicks, stats.mass_mailing_id AS id
            FROM mail_mail_statistics AS stats
            LEFT OUTER JOIN link_tracker_click AS clicks ON clicks.mail_stat_id = stats.id
            WHERE stats.mass_mailing_id IN %s
            GROUP BY stats.mass_mailing_id
        """, (tuple(self.ids), ))

        mass_mailing_data = self.env.cr.dictfetchall()
        mapped_data = dict([(m['id'], 100 * m['nb_clicks'] / m['nb_mails']) for m in mass_mailing_data])
        for mass_mailing in self:
            mass_mailing.clicks_ratio = mapped_data.get(mass_mailing.id, 0)

    # --------
    # ONCHANGE
    # --------
    @api.onchange('mass_mailing_campaign_id')
    def _onchange_mass_mailing_campaign_id(self):
        if self.mass_mailing_campaign_id:
            dic = {'campaign_id': self.mass_mailing_campaign_id.campaign_id,
                   'source_id': self.mass_mailing_campaign_id.source_id,
                   'medium_id': self.mass_mailing_campaign_id.medium_id}
            self.update(dic)

    # ----------
    # CONSTRAINS
    # ----------
    @api.constrains('email_template_id')
    def _constraint_email_template_id(self):
        for r in self:
            if r.email_template_id and not r.email_template_id.fso_email_template:
                raise ValidationError("The field fso_email_template is not set! "
                                      "The email template must be an fso_email_template!")

    # Prevent using the same email template twice (roughly a one2one implementation)
    # ATTENTION: The limitation to use an e-mail template only once may be removed at any time
    #            Since mail.mass_mailing already has it's own fields for 'subject', 'reply_to' and 'email_from'
    #            there is no real reason to restrict one e-mail template to one mass mailing.
    _sql_constraints = [('email_template_id_unique', 'unique(email_template_id)',
                         'E-Mail Template already in use by another mass mailing.\n'
                         'Remove it from the other mass mailing first or make a copy of the email template!')]

    # -------
    # ACTIONS
    # -------
    @api.multi
    def action_edit_html(self):
        """ Normally this would edit the body_html field of the mass mailing. If no body_html content exits
            the original mass mailing addon would send you to an email template select page and then copy the body of
            the email template to the body field of mass_mailing. From then only the body field of the mass mailing
            would be changed but no longer the email template.

            This system has the advantage that one could start from an e-mail template but then customize everything
            for the mass mailing. The disadvantage is that one may expect that a change to the template would
            also change the mass mailing(s) that are using this template
        :return:
        """
        if not self.ensure_one():
            raise ValueError('One and only one ID allowed for this action')

        # If this mass mailing is not connected to an fso email template do the "regular" thing
        if not self.email_template_id:
            return super(MassMailing, self).action_edit_html()

        # Open the FS-Online E-Mail Editor
        #
        # /web#id=13&view_type=form&model=mail.mass_mailing&action=586
        return_url = '/web#id=%s&view_type=form&model=mail.mass_mailing&action=%s' \
                     '' % (self.id, self.env.context['params']['action'])
        return_url_quoted = urllib.quote(return_url, safe='')

        url = "/fso/email/edit?template_id=%s&enable_editor=1&return_url=%s" \
              "" % (self.email_template_id.id, return_url_quoted)
        return {
            'name': _('Open with Visual Editor'),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    # --------------
    # Record Methods
    # --------------
    @api.multi
    def convert_links(self):
        res = {}
        for mass_mailing in self:
            utm_mixin = mass_mailing.mass_mailing_campaign_id if mass_mailing.mass_mailing_campaign_id else mass_mailing
            html = mass_mailing.body_html if mass_mailing.body_html else ''

            vals = {'mass_mailing_id': mass_mailing.id}

            if mass_mailing.mass_mailing_campaign_id:
                vals['mass_mailing_campaign_id'] = mass_mailing.mass_mailing_campaign_id.id
            if utm_mixin.campaign_id:
                vals['campaign_id'] = utm_mixin.campaign_id.id
            if utm_mixin.source_id:
                vals['source_id'] = utm_mixin.source_id.id
            if utm_mixin.medium_id:
                vals['medium_id'] = utm_mixin.medium_id.id

            res[mass_mailing.id] = self.env['link.tracker'].convert_links(html, vals, blacklist=['/unsubscribe_from_list'])

        return res

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, vals):

        # Copy fso_email_html_odoo from template to body_html field of mass mailing
        if vals.get('email_template_id'):
            fso_email_template = self.env['email.template'].browse([vals.get('email_template_id')])
            vals['body_html'] = fso_email_template.fso_email_html_odoo

        # Update body html by email_template_id.fso_email_html_odoo
        return super(MassMailing, self).create(vals=vals)

    @api.multi
    def write(self, vals):

        # Copy fso_email_html_odoo from template to body_html field of mass mailing
        if vals.get('email_template_id'):
            fso_email_template = self.env['email.template'].browse([vals.get('email_template_id')])
            vals['body_html'] = fso_email_template.fso_email_html_odoo

        return super(MassMailing, self).write(vals=vals)
