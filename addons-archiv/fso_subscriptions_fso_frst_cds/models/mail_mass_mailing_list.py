# -*- coding: utf-8 -*-

from openerp import models, fields, api

class MailMassMailingListCDS(models.Model):
    _inherit = "mail.mass_mailing.list"

    frst_zverzeichnis_id = fields.Many2one(string="zVerzeichnis",
                                           comodel_name="frst.zverzeichnis",
                                           help="FundraisingStudio marketing campaign")
