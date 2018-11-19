# -*- coding: utf-'8' "-*-"
from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class Altruja(models.Model):
    _name = "altruja"

    # ------
    # FIELDS
    # ------
    state = fields.Selection(selection=[('new', 'New'),
                                         ('error', 'Error'),
                                         ('done', 'Done'),
                                         ('skipped', 'Skipped'),
                                         ('synced', 'Synced')],
                              string="State",
                              readonly=True)

    # Check if the same job exits already
    skipped = fields.One2many(comodel_name='altruja', inverse_name='skipped_by', readonly=True)
    skipped_by = fields.Many2one(comodel_name='altruaj', inverse_name='skipped', readonly=True)

    # Errors and exceptions
    error_type = fields.Selection([('exception', 'Exception'),
                                   ('unknown_fields', 'Unknown Fields')],
                                  string="Error Type",
                                  readonly=True)
    error_details = fields.Text(string='Error Details',
                                readonly=True)

    # Linking and info
    partner_id = fields.Many2one(comodel_name='res.partner',
                                 readonly=True)                        # TODO: Inverse Field
    partner_matching_details = fields.Text('Partner Matching Details',
                                           help="Details about the partner matching process",
                                           readonly=True)

    sale_order_id = fields.Many2one(comodel_name='sale.order', readonly=True)                      # TODO: Inverse Field
    sale_order_line_id = fields.Many2one(comodel_name='sale.order.line', readonly=True)            # TODO: Inverse Field
    payment_transaction_id = fields.Many2one(comodel_name='payment.transaction', readonly=True)    # TODO: Inverse Field
    bank_id = fields.Many2one(comodel_name='res.partner.bank', readonly=True)                      # TODO: Inverse Field

    # Altruja Fields
    # --------------
    altruja_status = fields.Char('Altruja Status', readonly=True)
    datum = fields.Char('Datum', readonly=True)                                # ACHTUNG: = Buchungsdatum = Payment Transaction Datum!

    anonym = fields.Char('Anonym', readonly=True)                              # Derzeit nicht verarbeitet
    rechnungsnummer = fields.Char('Rechnungsnummer', readonly=True)            # Derzeit nicht verarbeitet
    wirecard_zeitraum = fields.Char('Wirecard-Zeitraum', readonly=True)        # Derzeit nicht verarbeitet
    quittungavailableat = fields.Char('Quittungavailableat', readonly=True)    # Derzeit nicht verarbeitet
    selbst_buchen = fields.Char('Selbst buchen', readonly=True)                # Derzeit nicht verarbeitet

    sonderwert_1 = fields.Char('sonderwert_1', readonly=True)                  # Derzeit nicht verarbeitet
    sonderwert_2 = fields.Char('sonderwert_2', readonly=True)                  # Derzeit nicht verarbeitet
    sonderwert_3 = fields.Char('sonderwert_3', readonly=True)                  # Derzeit nicht verarbeitet

    # res.partner
    firma = fields.Char('Firma', readonly=True)                                # Extra res.partern fuer Firma aufbauen
    vorname = fields.Char('Vorname', readonly=True)
    nachname = fields.Char('Nachname', readonly=True)
    email = fields.Char('Email', readonly=True)

    strasse = fields.Char('Strasse', readonly=True)
    adresszusatz = fields.Char('Adresszusatz', readonly=True)
    postleitzahl = fields.Char('Postleitzahl', readonly=True)
    ort = fields.Char('Ort', readonly=True)
    land = fields.Char('Land', readonly=True)

    geburtsdatum = fields.Char('Geburtsdatum', readonly=True)

    kontakt_erlaubt = fields.Char('Kontakt erlaubt', readonly=True)
    spendenquittung = fields.Char('Spendenquittung', readonly=True)         # Nicht mehr benoetig

    # res.partner.bank
    iban = fields.Char('IBAN', readonly=True)
    bic = fields.Char('BIC', readonly=True)
    kontoinhaber = fields.Char('Kontoinhaber', readonly=True)                              # TODO: Add field to payment_frst ?!?

    # sale.order
    spenden_id = fields.Integer('Spenden-ID', index=True, readonly=True)                   # EXTERNAL ID OF THE RECORD
    erstsspenden_id = fields.Char('Erstsspenden-ID', readonly=True,
                                  help="Entspricht dem ersten Auftrag bei wiederkehrenden Spenden (Vertrag)")
    waehrung = fields.Selection(string='Waehrung',
                                selection=[('EUR', 'EUR')], required=True, readonly=True)        # Only 'EUR' is allowed

    # sale.order.line
    spenden_typ = fields.Char('Spenden-Typ', readonly=True)                # Aendern auf Selection field
    spendenbetrag = fields.Float('Spendenbetrag', required=True, readonly=True)
    intervall = fields.Char('Intervall', readonly=True)                    # Aebhaengig von Spenden_Typ

    seiten_id = fields.Char('Seiten-ID', readonly=True)                    # Derzeit nicht verarbeitet
    Seitenname = fields.Char('Seitenname', readonly=True)                  # FRST Verarbeitung ZVerz.

    # payment.transaction
    quelle = fields.Char('Quelle',
                         help="z.B.: Online (Wirecard/Lastschrift)", readonly=True)    # Payment Methode (Werte?!?)

    # --------------------------
    # CONSTRAINTS AND VALIDATION
    # --------------------------
    # https://www.postgresql.org/docs/9.3/static/ddl-constraints.html
    _sql_constraints = [
        ('spenden_id_unique', 'UNIQUE(spenden_id)', "'spenden_id' must be unique!"),
    ]

