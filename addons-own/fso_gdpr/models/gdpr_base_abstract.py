# -*- coding: utf-8 -*-
from openerp import models, fields


class GDPRBase(models.AbstractModel):
    _name = "gdpr.base"

    gdpr_accepted = fields.Boolean(string="GDPR accepted",
                                    help="This field can be used on webforms to collect the gdpr consent of the"
                                         "partner")
