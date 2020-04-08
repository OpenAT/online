# -*- coding: utf-8 -*-

from openerp import models, fields


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    frst_groups_bestaetigung_emails = fields.One2many(comodel_name="frst.zgruppedetail",
                                                      inverse_name="bestaetigung_email",
                                                      string='Used by FRST Groups')

    frst_groups_bestaetigung_success_email = fields.One2many(comodel_name="frst.zgruppedetail",
                                                             inverse_name="bestaetigung_success_email",
                                                             string='Used by FRST Groups')

    frst_groups_subscription_email = fields.One2many(comodel_name="frst.zgruppedetail",
                                                     inverse_name="subscription_email",
                                                     string='Used by FRST Groups')
