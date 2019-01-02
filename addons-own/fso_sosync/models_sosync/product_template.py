# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductTemplateSosync(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "base.sosync"]

    name = fields.Char(sosync="True")
    active = fields.Boolean(sosync="True")

    # Verkaufsbeschreibung (in Angeboten oder auf der Webseiten bei einigen Templates)
    description_sale = fields.Char(sosync="True")

    # Z.B.: Spende, Patenschaft, ...
    fs_product_type = fields.Selection(sosync="True")

    # Fundraising Studio Gruppe (zGruppeDetail) (TO: fs.group)
    # TODO: FS-Groups may be redesigned!
    #fs_group_ids = fields.Many2many(sosync="True")

    # Webseiten Template z.B.: OPC oder Spendenlayout
    product_page_template = fields.Selection(sosync="True")

    # Typ z.B.: "Verbrauchsmaterial" oder "Dienstleistung"
    type = fields.Selection(sosync="True")

    # Verkaufseinheit z.B.: Stueck oder Liter (TO: product.uom)
    uom_id = fields.Many2one(sosync="True")

    # Relative Web URL z.B.: /shop/product/8
    website_url = fields.Char(sosync="True")

    # Verkaufspreis oder Standard-Spendenhoehe
    list_price = fields.Float(sosync="True")

    # list_price Hoehe frei waehlbar z.B. fuer Spenden
    price_donate = fields.Boolean(sosync="True")

    # Mindestwert fuer list_price
    price_donate_min = fields.Integer(sosync="True")

    # Spendenbuttons oder Spendenhoehenvorschlaege (TO: product.website_price_buttons)
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #price_suggested_ids = fields.One2many(sosync="True")

    # Standard (vorausgewaehltes) Zahlungsintervall (TO: product.payment_interval)
    payment_interval_default = fields.Many2one(sosync="True")

    # Erlaubte Zahlungsintervalle (TO: product.payment_interval_lines)
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #payment_interval_lines_ids = fields.One2many(sosync="True")

    # Zahlungsmethoden Overwrite beim Produkt (TO: product.acquirer_lines)
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #product_acquirer_lines_ids = fields.One2many(sosync="True")

    # Soll die Produktseite auf der Webseite angezeigt werden
    website_published = fields.Boolean(sosync="True")
    website_published_start = fields.Datetime(sosync="True")
    website_published_end = fields.Datetime(sosync="True")

    # Berechnetes Feld auf der Basis von website_published, website_published_start und website_published_end
    website_visible = fields.Boolean(sosync="True")

