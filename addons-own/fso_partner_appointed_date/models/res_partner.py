# -*- coding: utf-8 -*-
from openerp import models, fields, api

import logging
logger = logging.getLogger(__name__)


class FSOResPartnerAppointedDate(models.Model):
    _inherit = "res.partner"

    appointed_date = fields.Date(string="Appointed date")

    def create_appointed_date_mail_message(self, partner, values):
        appointed_date = values.get('appointed_date')
        if appointed_date:
            date_iso = appointed_date.strftime("%Y-%m-%d")
            logger.debug("Found appointed date: %s" % date_iso)
            partner.sudo().with_context(mail_post_autofollow=False).message_post(
                body=date_iso,
                type='comment',
                subtype='fso_mail_message_subtypes_appointed_date.fson_appointed_date',
                content_subtype='plaintext')

    @api.model
    def create(self, values):
        partner = super(FSOResPartnerAppointedDate, self).create(values)
        self.create_appointed_date_mail_message(partner, values)
        return partner

    @api.multi
    def write(self, values):
        res = super(FSOResPartnerAppointedDate, self).write(values)

        for p in self:
            self.create_appointed_date_mail_message(p, values)

        return res
