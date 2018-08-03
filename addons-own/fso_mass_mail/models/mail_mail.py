# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import werkzeug.urls

from openerp import api, fields, models, tools

from openerp.addons.link_tracker.models.link_tracker import URL_REGEX

class MailMail(models.Model):
    """Integrate mail tracking urls to mass mailing mails"""
    _inherit = ['mail.mail']

    @api.multi
    def send_get_mail_body(self, partner=None):
        """ Add statistics_ids to link_tracker urls """
        self.ensure_one()

        body = super(MailMail, self).send_get_mail_body(partner=partner)

        # Add statistics_ids to link_tracker urls
        if self.mailing_id and body and self.statistics_ids:
            for match in re.findall(URL_REGEX, self.body_html):
                href = match[0]
                url = match[1]

                parsed = werkzeug.urls.url_parse(url, scheme='http')

                if parsed.scheme.startswith('http') and parsed.path.startswith('/r/'):
                    new_href = href.replace(url, url + '/m/' + str(self.statistics_ids[0].id))
                    body = body.replace(href, new_href)

        return body
