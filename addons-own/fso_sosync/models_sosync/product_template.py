# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ProductTemplateSosync(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "base.sosync"]

    # This model is read-only in FRST

    name = fields.Char(sosync="fson-to-frst")
    default_code = fields.Char(sosync="fson-to-frst")
    active = fields.Boolean(sosync="fson-to-frst")

    # Verkaufsbeschreibung (in Angeboten oder auf der Webseiten bei einigen Templates)
    description_sale = fields.Char(sosync="fson-to-frst")

    # Z.B.: Spende, Patenschaft, ...
    fs_product_type = fields.Selection(sosync="fson-to-frst")

    # Fundraising Studio Gruppe (zGruppeDetail) (TO: fs.group)
    # DEPRECATED use zgruppedetail_ids fso_frst_groups
    #fs_group_ids = fields.Many2many(sosync="fson-to-frst")

    # New Group System (frst.zgruppedetail)
    zgruppedetail_ids = fields.Many2many(sosync="fson-to-frst")

    # Webseiten Template z.B.: OPC oder Spendenlayout
    product_page_template = fields.Selection(sosync="fson-to-frst")

    # Typ z.B.: "Verbrauchsmaterial" oder "Dienstleistung"
    type = fields.Selection(sosync="fson-to-frst")

    # Verkaufseinheit z.B.: Stueck oder Liter (TO: product.uom)
    uom_id = fields.Many2one(sosync="fson-to-frst")

    # Relative Web URL z.B.: /shop/product/8
    website_url = fields.Char(sosync="fson-to-frst")

    # Verkaufspreis oder Standard-Spendenhoehe
    list_price = fields.Float(sosync="fson-to-frst")

    # list_price Hoehe frei waehlbar z.B. fuer Spenden
    price_donate = fields.Boolean(sosync="fson-to-frst")

    # Mindestwert fuer list_price
    price_donate_min = fields.Integer(sosync="fson-to-frst")

    # Spendenbuttons oder Spendenhoehenvorschlaege (TO: product.website_price_buttons)
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #price_suggested_ids = fields.One2many(sosync="fson-to-frst")

    # Standard (vorausgewaehltes) Zahlungsintervall (TO: product.payment_interval)
    payment_interval_default = fields.Many2one(sosync="fson-to-frst")

    # Erlaubte Zahlungsintervalle (TO: product.payment_interval_lines)
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #payment_interval_lines_ids = fields.One2many(sosync="fson-to-frst")

    # Zahlungsmethoden Overwrite beim Produkt (TO: product.acquirer_lines)
    # ATTENTION: One2Many fields do NOT exist in the DB and are not relevant for the sync ONLY the inverse many2One
    #            field is important and should trigger the child job(s)
    #product_acquirer_lines_ids = fields.One2many(sosync="fson-to-frst")

    # Soll die Produktseite auf der Webseite angezeigt werden
    website_published = fields.Boolean(sosync="fson-to-frst")
    website_published_start = fields.Datetime(sosync="fson-to-frst")
    website_published_end = fields.Datetime(sosync="fson-to-frst")

    # Berechnetes Feld auf der Basis von website_published, website_published_start und website_published_end
    website_visible = fields.Boolean(sosync="fson-to-frst")

    giftee_form_id = fields.Many2one(sosync="fson-to-frst")
    giftee_email_template = fields.Many2one(sosync="fson-to-frst")

    categ_id = fields.Many2one(sosync="fson-to-frst")
