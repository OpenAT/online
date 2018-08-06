# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import werkzeug.urls

from openerp import api, fields, models, tools

from openerp.addons.link_tracker.models.link_tracker import URL_REGEX


class MailMail(models.Model):
    """Integrate mail tracking urls to mass mailing mails"""
    _inherit = ['mail.mail']

    @api.model
    def send_get_mail_body(self, mail, partner=None):
        """ This method will be called only when the e-mail gets send (mail.mail .send())

            Add the statistics_id to all link_tracker urls
            with this statistics_id every send e-mail can be tracked individually

            The corresponding route can be found under controllers/main.py
        """

        body = super(MailMail, self).send_get_mail_body(mail=mail, partner=partner)

        # Add statistics_ids to link_tracker urls
        if mail.mailing_id and body and mail.statistics_ids:
            for match in re.findall(URL_REGEX, mail.body_html):
                href = match[0]
                url = match[1]

                parsed = werkzeug.urls.url_parse(url, scheme='http')

                if parsed.scheme.startswith('http') and parsed.path.startswith('/r/'):
                    new_href = href.replace(url, url + '/m/' + str(mail.statistics_ids[0].id))
                    body = body.replace(href, new_href)

        return body
