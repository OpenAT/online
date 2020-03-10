# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FRSTzVerzeichnisMailMassMailingList(models.Model):
    _inherit = "frst.zverzeichnis"

    mass_mailing_list_ids = fields.One2many(string="Mailing Lists",
                                            comodel_name='mail.mass_mailing.list',
                                            inverse_name='frst_zverzeichnis_id',
                                            readonly=True)
