
## Update Process:
- start odoo with -u all
- install fsonline
- uninstall base_config
- uninstall base_mod (felder für instance_port ist in fso_base übernommen)
- uninstall payment_postfinance (for all AT Instances)
- stop odoo
- start odoo with -i fso_base
- uninstall fs_groups
- uninstall website_as_widget
- uninstall website_base_setup (Todo: Write replacement website_robotstxt)
- uninstall website_sale_payment_fix
- uninstall website_tools
- stop odoo
- start odoo with -u all

## Test after update:
- Öffnen alle backend views ohne Fehlermeldung (partner, product, ...)
- Sind birthday_web und andere res.partner *_web felder noch mit ihren daten befüllt
- Kann man ein neues Spendenprodukt anlegen sowie varianten davon
- Kann man weiterhin die Checkout und Billing fields bearbeiten meine-daten fields
- Öffnen sich alle Seiten der Webseite ohne Fehler (und auch ohne Fehler im Log)
- Funktioniert die Einschränkung der Payment Provider per JS bei der Auswahl Spendenintervallen
- Funktioniert beim Checkout/Billing die Frontend Validierung der Felder
- Funktioniert bei /meine-daten die Frontend Validierung der Felder
- Kann ein Checkout Prozess bis zum Ende durchgezogen werden
- Sind nach dem Checkout Vorgange alle Daten vorhanden (Sale Order, Payment, ...)
