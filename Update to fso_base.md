
## Update Process:
Open two ssh shells all the time so you could permanently watch all log messages while updating!

Prerequisites
- Create a snapshot of the server
- Run a salt highstate just for the online(x) host to setup new python libs
- Inform the customer about the downtime (on production instances)
- Manually provide the FS-Online base (cp old source then git checkout o8r53)

Update
- Create an up to date backup of the database (like the cronjob does)
- Make screenshots of the website menu, checkout fields, billing fields, apf fields and settings
- stop the instance service (e.g.: service care stop)
- Disable the webhook on github
- change instance.ini to the correct odoo core ON GITHUB! (e.g.: o8r53)
- update the instance repo from github (git fetch; git pull)
- start instance with -u all (by changing init.d file first and then starting the service)
- GUI: install fsonline
- GUI: export the fs_groups names
- GUI: uninstall base_config
- GUI: uninstall base_mod (felder für instance_port ist in fso_base übernommen)
- GUI: uninstall payment_postfinance for all Austria Instances
- GUI: uninstall fs_groups
- stop instance (e.g.: service care stop)
- start instance with -i fso_base (again change init file of instance and start service)
- GUI: uninstall website_as_widget
- GUI: uninstall website_base_setup (Todo: Write replacement website_robotstxt)
- GUI: uninstall website_sale_payment_fix
- GUI: uninstall website_tools
- GUI OPTIONAL: install website_widget_manager and configure domains and widgets
- stop instance (e.g.: service care stop)
- start instance with -u all (again by changing init file and service start)
- GUI: import the fs_group names from former export

After the Update
- remove -u all from init file
- enable the webhook on github again
- do all tests in "Test after update" further down for production databases
- restore/check website menu, checkout fields, billing fields, apf fields and settings
- optional: test all widgets on external pages
- optional: inform the customer that everything is up and running again (on production instances)

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
