# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class Altruja(models.Model):
    _name = "altruja"

    # ------
    # FIELDS
    # ------
    status = fields.Selection(selection=[('new', 'New'),
                                         ('error', 'Error'),
                                         ('done', 'Done'),
                                         ('skipped', 'Skipped'),
                                         ('synced', 'Synced')])

    # Check if the same job exits already
    skipped = fields.One2many(comodel_name='altruja', inverse_name='skipped_by')
    skipped_by = fields.One2many(comodel_name='altruaj', inverse_name='skipped')

    # Errors and exceptions
    error_type = fields.Selection([('exception', 'Exception'),
                                   ('unknown_fields', 'Unknown Fields'),
                                   ])
    error_details = fields.Text('Error Details')

    # Linking and info
    partner_id = fields.Many2one(comodel_name='res.partner')                        # TODO: Inverse Field
    partner_matching_details = fields.Text('Partner Matching Details',
                                           help="Details about the partner matching process")

    sale_order_id = fields.Many2one(comodel_name='sale.order')                      # TODO: Inverse Field
    sale_order_line_id = fields.Many2one(comodel_name='sale.order.line')            # TODO: Inverse Field
    payment_transaction_id = fields.Many2one(comodel_name='payment.transaction')    # TODO: Inverse Field
    bank_id = fields.Many2one(comodel_name='res.partner.bank')                      # TODO: Inverse Field

    # Altruja Fields
    # --------------
    altruja_status = fields.Char('Altruja Status')
    datum = fields.Char('Datum')

    anonym = fields.Char('Anonym')
    rechnungsnummer = fields.Char('Rechnungsnummer')
    wirecard_zeitraum = fields.Char('Wirecard-Zeitraum')
    quittungavailableat = fields.Char('Quittungavailableat')
    selbst_buchen = fields.Char('Selbst buchen')

    sonderwert_1 = fields.Char('sonderwert_1')
    sonderwert_2 = fields.Char('sonderwert_2')
    sonderwert_3 = fields.Char('sonderwert_3')

    # res.partner
    firma = fields.Char('Firma')
    vorname = fields.Char('Vorname')
    nachname = fields.Char('Nachname')
    email = fields.Char('Email')

    strasse = fields.Char('Strasse')
    adresszusatz = fields.Char('Adresszusatz')
    postleitzahl = fields.Char('Postleitzahl')
    ort = fields.Char('Ort')
    land = fields.Char('Land')

    geburtsdatum = fields.Char('Geburtsdatum')

    kontakt_erlaubt = fields.Char('Kontakt erlaubt')
    spendenquittung = fields.Char('Spendenquittung')

    # res.partner.bank
    iban = fields.Char('IBAN')
    bic = fields.Char('BIC')
    kontoinhaber = fields.Char('Kontoinhaber')                              # TODO: Add field to payment_frst ?!?

    # sale.order
    spenden_id = fields.Integer('Spenden-ID', index=True)
    erstsspenden_id = fields.Char('Erstsspenden-ID',
                                  help="Entspricht dem Ersten Auftrag bei wiederkehrenden Spenden (Vertrag)")
    waehrung = fields.Char('Währung', required=True)

    # sale.order.line
    Spenden_Typ = fields.Char('Spenden-Typ')
    spendenbetrag = fields.Float('Spendenbetrag', required=True)
    intervall = fields.Char('Intervall')

    seiten_id = fields.Char('Seiten-ID')
    Seitenname = fields.Char('Seitenname')

    # payment.transaction
    quelle = fields.Char('Datum',
                         help="z.B.: Online (Wirecard/Lastschrift)")
