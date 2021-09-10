# -*- coding: utf-'8' "-*-"
__author__ = 'Michael Karrer'
from openerp import models, fields


class MailMessage(models.Model):
    _inherit = "mail.message"

    subtype_xml_id = fields.Char(string="Subtype XML ID",
                                 related="subtype_id.xml_id",
                                 store=False)

