# -*- coding: utf-8 -*-
from openerp import models, fields, api


import logging
logger = logging.getLogger(__name__)


class FRSTxBankverbindung(models.Model):
    """
    The FundraisingStudio xBankverbindung.
    """
    _name = "frst.xbankverbindung"

    beschreibung = fields.Char(string="Beschreibung")
    kurzbezeichnung = fields.Char(string="Kurzbezeichnung")
    bankleitzahl = fields.Char(string="Bankleitzahl")
    kontonummer = fields.Char(string="Kontonummer")
    xiban = fields.Char(string="IBAN")
