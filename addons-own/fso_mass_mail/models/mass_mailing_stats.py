# -*- coding: utf-'8' "-*-"

from openerp import api, models, fields
from openerp.exceptions import ValidationError
from openerp.tools.translate import _

import urllib


class MassMailingStats(models.Model):
    _inherit = "mail.mail.statistics"

    # Link tracking
    links_click_ids = fields.One2many('link.tracker.click', 'mail_stat_id', string='Links click')
    clicked = fields.Datetime(help='Date when customer clicked on at least one tracked link')
    # Status
    state = fields.Selection(compute="_compute_state",
                             selection=[('outgoing', 'Outgoing'),
                                        ('exception', 'Exception'),
                                        ('sent', 'Sent'),
                                        ('opened', 'Opened'),
                                        ('replied', 'Replied'),
                                        ('bounced', 'Bounced')],
                             store=True)
    state_update = fields.Datetime(compute="_compute_state", string='State Update',
                                    help='Last state update of the mail',
                                    store=True)
    recipient = fields.Char(compute="_compute_recipient")

    @api.depends('sent', 'opened', 'clicked', 'replied', 'bounced', 'exception')
    def _compute_state(self):
        self.update({'state_update': fields.Datetime.now()})
        for stat in self:
            if stat.exception:
                stat.state = 'exception'
            elif stat.sent:
                stat.state = 'sent'
            elif stat.opened or stat.clicked:
                stat.state = 'opened'
            elif stat.replied:
                stat.state = 'replied'
            elif stat.bounced:
                stat.state = 'bounced'
            else:
                stat.state = 'outgoing'

    def _compute_recipient(self):
        for stat in self:
            if stat.model not in self.env:
                continue
            target = self.env[stat.model].browse(stat.res_id)
            if not target or not target.exists():
                continue
            email = ''
            for email_field in ('email', 'email_from'):
                if email_field in target and target[email_field]:
                    email = ' <%s>' % target[email_field]
                    break
            stat.recipient = '%s%s' % (target.display_name, email)

    def set_clicked(self, mail_mail_ids=None, mail_message_ids=None):
        stat_ids = self._get_ids(mail_mail_ids, mail_message_ids, [('clicked', '=', False)])
        statistics = self.browse(stat_ids)
        statistics.write({'clicked': fields.Datetime.now()})
        return statistics
