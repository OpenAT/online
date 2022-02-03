# -*- coding: utf-8 -*-
from openerp import models, fields, api


import logging
logger = logging.getLogger(__name__)


class FRSTxBankverbindungSosync(models.Model):
    _name = "frst.xbankverbindung"
    _inherit = ["frst.xbankverbindung", "base.sosync"]

    beschreibung = fields.Char(sosync="frst-to-fson")
    kurzbezeichnung = fields.Char(sosync="frst-to-fson")
    bankleitzahl = fields.Char(sosync="frst-to-fson")
    kontonummer = fields.Char(sosync="frst-to-fson")
    xiban = fields.Char(sosync="frst-to-fson")
