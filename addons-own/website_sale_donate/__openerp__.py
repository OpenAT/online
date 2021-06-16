# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "FS-Online Spendenshop",
    'version': '2.6',
    'summary': """Shoperweiterungen für Fundraising Studio Community""",
    'sequence': 200,
    'description': """

Anpassungen des Online-Shops für NPOs
=====================================

- Frei wählbarer Produktpreis
- Minimaler Betrag für freien Produktpreis kann festgelegt werden (wird in Form mit JS und bei POST-Data kontrolliert)
- Produktpreis kann in Produktübersichten ausgeblendet werden
- Produktmengenselektor kann ausgeblendet werden
- Zahlungsbox (Add to cart) kann für Produkte ausgeblendet werden
- Zahlungsintervalle sind beim Produkt festlegbar
- Zahlungsintervalle können frei konfiguriert werden (Standardzahlungsintervalle werden automatisch vor-angelegt)
- Zahlungsintervall XMLID (externalid) Zahlungsintervall Name und arbitrary price werden in der so line gespeichert
- Direkter Checkout von Produkten ist einstellbar
- Forced Fields der Kontaktdaten können geändert werden!
- Standard Spendenprodukt wird angelegt (Donate)
- Standard Lieferart wird angelegt (None)
- Kontaktdaten werden auch mittels jquery validate überprüft! (Deaktiviert in templates.xml)
- Ausblenden der Steuer und Lieferkosten über Java Script wenn kleiner gleich 0 (nur in der cart page!)
- Lieferart ausblendbar per Checkbox
- Lieferadresse ausblendbar per Checkbox
- Wording für EN und DE im Shop auf NPOs ausgelegt!
- CROWDFUNDING Addons
- Eigenes Donation Product-Page Layout
- Hintergrund Parallax-Bild für das Donation Page Layout
- Verbesserte Spenden List Views für alle Responsive-Auflösungen
- Automatische Thumbnail Generierung (Image Square)
- Über Checkboxen kann fast alles ein oder ausgeblendet werden.
- Inline-Hilfe bei den Spenden Einstellungen
- Image Feld bei products.product speichert original Auflösung
- Neue Info-Buttons beim Produkt für die gesamte Spendenhöhe

## Todo
- User Form (controller) to create new donation campaigns
- store product images on disk and not in the db

## website_sale_payment_fix was integrated here
This addon fixes the session depended payment process of odoo 8.0 website_sale shop in combination with the
payment_ogone_dadi payment provider which is a replacement of the odoo ogone payment provider.

The problem of the original odoo payment process is that the update of the payment transaction and the related sales
order is dependent on the data of the current request.session. But it might be that the answer from ogone is received
later and not related to the current session at all and also send by ogone multible times for the same or different
states of the particular payment.transaction.

To solve this we did:
- **clear the session variables** sale_order_id, sale_last_order_id, sale_transaction_id, sale_order_code_pricelist_id
  so a new Sales Order would be generated if the user opens the shop again.
  AND **set the sales order to state bestätigt** so that no changes are possible
  after the button of the PP in shop/payment is pressed (JSON calls method payment_transaction in website_sale main.py)

- If we receive an answer from the PP **all the logic for the Sales Order is done at method form_feedback** (website_sale
  did this already partially for setting the SO to state done but did not react to all possible states) so we do no
  longer depend on /shop/payment/validate to set the other states for the SO. This was needed because payment_validate
  did use session variables to find the payment.transaction and the sales.order but since the answer of the PP can be
  defered this is not always correct.

- All the other stuff is done in the addon payment_ogone_dadi - read its description too!

    """,
    'author': "Datadialog - Michael Karrer",
    'website': "http://www.datadialog.net/",
    'category': 'Uncategorized',
    'depends': [
        'product',
        'sale',
        'fso_base',
        'fso_base_website',
        'payment',
        'website_sale',
        'website_sale_delivery',
        'website_sale_categories',
        'website_event',
        'website_blog',
        'auth_partner',
        #'fso_frst_groups', is included in fso_base
        'fso_forms',
    ],
    'installable': True,
    'data': [
        'data/payment_intervals.xml',
        'data/data.xml',
        #'data/email_template_data.xml', # moved to fso_base
        'security/ir.model.access.csv',
        'views/payment_acquirer.xml',

        'views/templates.xml',
        'views/templates_10_small_cart.xml',
        'views/templates_20_crowdfunding.xml',
        'views/templates_30_product_listings.xml',
        'views/templates_35_donation_button_templates_and_snippets.xml',
        'views/templates_40_product_page.xml',

        'views/templates_50_ppt_subtemplates.xml',
        'views/templates_51_ppt_donate.xml',
        'views/templates_52_ppt_ahch.xml',
        'views/templates_53_ppt_opc.xml',
        'views/templates_54_ppt_inline_donation.xml',

        'views/templates_60_step_indicator.xml',
        'views/templates_61_cart.xml',
        'views/templates_62_checkout.xml',
        'views/templates_63_payment.xml',
        'views/templates_64_thanks.xml',

        'views/views.xml',
        'views/sale_order_line.xml',
        'views/website.xml',
        'views/sale_order.xml',
        'views/product_public_category.xml',
        #'views/fsonline_menu.xml', # Moved to fsonline addon
        'data/run_on_install_update.xml'        # Update xml_id field on update and install
    ],
    'post_init_hook': 'post_init_hook',         # Update xml_id field on install (same as above but only on install)
}
