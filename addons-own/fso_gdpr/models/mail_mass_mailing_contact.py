# -*- coding: utf-'8' "-*-"
from openerp import models


class MassMailingContactGDPRBase(models.Model):
    _name = 'mail.mass_mailing.contact'
    _inherit = ['mail.mass_mailing.contact', 'gdpr.base']
