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

    @api.multi
    def name_get(self):
        return [
            (
                record.id, "%s (%s)" % (
                    record.kurzbezeichnung,
                    "IBAN %s" % record.xiban if record.xiban else
                    "BLZ %s KTO %s" % (record.bankleitzahl, record.kontonummer) if record.bankleitzahl or record.kontonummer else
                    "Keine Kontoinformationen"
                )
            )
            for record in self
        ]
