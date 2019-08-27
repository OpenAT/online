# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.tools import SUPERUSER_ID

import logging
logger = logging.getLogger(__name__)


# Fundraising Studio groups
class FRSTzGruppeDetailApprovalMail(models.Model):
    _inherit = "frst.zgruppedetail"

    bestaetigung_email = fields.Many2one(string="Approval E-Mail Template",
                                         comodel_name='email.template',
                                         domain="[('fso_email_template', '=', True)]")
    bestaetigung_text = fields.Char(string="Approval Text", help="This text will be used for the print field "
                                                                 "%GruppenBestaetigungsText%")
    bestaetigung_thanks = fields.Html(string="Approval Thank You Page",
                                      help="If set this will be the html on the thank you page after a click on the "
                                           "approval link")

    @api.constrains('bestaetigung_erforderlich', 'bestaetigung_typ', 'bestaetigung_email')
    def constraint_bestaetigung_erforderlich(self):
        for r in self:
            if r.bestaetigung_erforderlich and r.bestaetigung_typ == 'doubleoptin':
                assert r.bestaetigung_email, _("'bestaetigung_erforderlich' is set and 'bestaetigung_typ' is "
                                               "'doubleoptin' but 'bestaetigung_email' is empty!")
            if r.bestaetigung_email:
                assert r.bestaetigung_email.fso_email_template, _("Approval Email Template must be a "
                                                                  "fso_email_template!")
                assert r.bestaetigung_email.fso_email_html_parsed and \
                       'GruppenBestaetigungsLink' in r.bestaetigung_email.fso_email_html_parsed, _(
                    "Print field %GruppenBestaetigungsLink% missing in 'fso_email_html_parsed'!")

    @api.onchange('bestaetigung_erforderlich', 'bestaetigung_typ', 'bestaetigung_email')
    def onchange_bestaetigung_erforderlich(self):
        for r in self:
            if r.bestaetigung_erforderlich and r.bestaetigung_typ == 'doubleoptin':
                if not r.bestaetigung_email:
                    default_approval_mail = self.env.ref('fso_frst_groups_email.email_template_group_approval',
                                                         raise_if_not_found=False)
                    if default_approval_mail:
                        r.bestaetigung_email = default_approval_mail.id
