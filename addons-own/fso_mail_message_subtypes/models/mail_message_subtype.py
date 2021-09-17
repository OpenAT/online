# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models


class MailMessageSubtype(models.Model):
    _name = "mail.message.subtype"
    _inherit = ["mail.message.subtype", "xml_id.field"]

