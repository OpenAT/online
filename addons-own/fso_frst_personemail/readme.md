# Fragen bzw. Anforderungen
Da wir mehrere E-Mails pro Person im FRST unterstützen ergeben sich folgende Fragen bzw. Anforderungen:

Webformulare und externe Systeme:
- Welche der E-Mail Adressen zeigen wir bei Webformularen bei denen nur eine E-Mail Adresse möglich ist
- Welche der E-Mail Adressen wird für den Datenaustausch mit externen Systemen verwendet die nur eine E-Mail
  pro Person unterstützen.
  
Datenimport
- Vorgehen beim Import von extern Personendaten mit nur einem Feld 'email' bei der Person

E-Mail als Login bzw Identitätsnachweis?
- Soll der Account/Login (res.user) unabhängig von der/den E-Mail Adressen gehalten werden
- Wenn mehrere E-Mails bei einer Person hinterlegt sind: Ist es sicher allen Adressen Tokens zu senden?

# Wichtige Info
Die E-Mail stellt mittlerweile so etwas wie den Primary-Key oder anders gesagt die Identität einer Person dar.
Sie ist in den meisten Fällen auch der Schlüssel zu jedweden Datenzugang (z.B.: vorausgefüllte Webformulare via Token
Link). Es muss Ihr daher eine besondere Aufmerksamkeit bei der Anlage, Änderung und beim Zusammenlegen zukommen.

Folgende Regeln würden uns die Arbeit erleichtern und die System-Sicherheit wesentlich verbessern:
- Personen mit unterschiedlichen (Haupt) E-Mail Adressen dürfen nicht automatisch zusammengelegt werden
- Eine Änderung der Hauptemailadresse kann nur durch
  - einen angemeldeten Web-User (via Token-Link oder FSO-Account),
  - oder eine Sachbearbeiter in FRST veranlasst werden
- Eine Änderung der Hauptemailadresse führt zu einem E-Mail Umzug
- Der odoo Account geht IMMER auf die Hauptemailadresse
- FS-Tokens werden nur für bestätigte Hauptemailadressen erzeugt und sind nur für best. HEA gültig!

Eine Ausnahme besteht wenn wir eine neue E-Mail Adresse bekommen und die bisherige Hauptemailadressen noch keinerlei
Verlinkungen (odoo Account, PersonEmailGruppe) hat und auch nicht per DOI bestätigt wurde. In diesem Fall wird die
aktueller E-Mail einfach zur neuen Hauptemailadresse.

## Erzwungene Zusammenlegung von Personen mit unterschiedlichen Hauptemailadressen
Werden vom FRST-Sachbearbeiter Personen mit untersch. Hauptemailadressen zusammengelegt wird versucht die verbeleibende
Hauptemailadressen automatisch zu bestimmen. Ist dies nicht eindeutig möglich muss der Sachbearbeiter die 
Hauptemailadressen festlegen um einen Merge durchführen zu können.

Folgende Regeln könnte man für die Bestimmung der neuen Hauptemailadresse (HEA) anwenden:
1. Nur einer der Beiden hat eine erzwungene Hauptemailadresse = neue HEA
2. Nur einer der Beiden hat einen verknüpften odoo Account = neue HEA
3. Nur einer der Beiden hat einen verknüpften odoo Account mit FS-Tokens = neue HEA
4. Nur einer der Beiden hat einen vernküfpten odoo Account mit FS-Tokens der für ein Login verwendet wurde = neue HEA
5. Nur einer der Beiden hat PersonEmailGruppen = neue HEA
6. Keine der Beiden hat eine erzwungene HEA, einen odoo Account oder PersonEmailGruppen -> Die Neuere wird zur HEA
7. Keine der Regeln trifft zu = Sachbearbeiter muss HEA festlegen

Diese Regeln werden einfach von oben nach unten durchgearbeitet! 

### Beispiel:
Regel 1: Person_A HEA und Person_B HEA haben beide keine erzwungene HEA = weiter zu Regel 2:\
Regel 2: Person_A HEA und Person_B HEA haben beide einen odoo Account = weiter zu Regel 3:\
Regel 3: Person_A HEA hat FS-Token, Person_B HEA hat keine = Person_A HEA wird zur HEA nach dem Merge
         Person_B HEA bleibt als PersonEmail erhalten da die E-Mails ja unterschiedlich sind






# Ziele
- Automatische Berechnung einer Hauptemailadresse
- (Todo) Manuelle (erzwungene) Festlegung der Hauptemailadresse
- Das Feld 'email' bei res.partner stimmt immer mit dem Feld 'email' der Haupt-PersonEmail überein
- Die Haupt-PersonEmail wird beim res.partner verlinkt (für Comfort und Kontrolle)
- Wir berechnen die Haupt-PersonEmail immer nach dem selben Schema!\
  (Es gibt daher keine gesonderten Regeln je nachdem *woher* die Daten
  oder Datenänderungen kommen. Ob die Daten von einem Import, einer Änderung im GUI
  oder durch den syncer angelegt oder verändert wurden ist also irrelevant)
- PersonEmail repariert sich wenn möglich selbst (z.B.: nach einem Merge oder bei bestehenden Datenfehlern)
- (Todo) Die Ermöglichung eines Umzuges einer PersonEmail

# Annahmen zu PersonEmail
Die folgenden Annahmen müssen noch von Harald und Sebastian bestätigt werden!
- Das Feld 'email' darf nach der Anlage nicht mehr geändert werden! Lediglich durch einen Umzug\
  (= Merge + Delete + Double-Opt-In) sollte man eine PersonEmail ändern können
- Das Feld 'partner_id' darf nach der Anlage nicht geändert werden (AUSNAHME: Merge)
- Nur die Felder 'gueltig_von' und 'gueltig_bis' und 'HEA erzwingen' dürfen nach der Anlage noch geändert werden\
  (abgesehen von berechneten Feldern wie 'main_email', 'state' oder 'last_email_update')
- Es gibt immer nur eine Hauptemailadresse pro Person
- Eine E-Mail darf pro Person nur einmal vorhanden sein
- Eine E-Mail kann mehrfach vorkommen wenn sie bei untersch. Personen zugeordnet ist

# Informationen zur Umsetzung
Um die Hauptemailadresse bestimmen zu können wird das Feld 'last_email_update' zu PersonEmail hinzugefügt.
Dieses Feld ermöglicht eine Sortierung der PersonEmails einer Person. Die gültige PersonEmail mit dem neuesten 
'last_email_update' Datum ist die Hauptemailadresse.

## Berechnung der Hauptemailadresse
Die Hauptemailadresse ist von 'last_email_update' und 'forced_main_address' abhängig. Während 'forced_main_address'
vom Benutzer oder dem System vergeben wird um die Hauptadresse zu erzwingen wird 'last_email_update' unter folgenden 
Umständen aktualisiert:
- Erstellung einer neuen gültigen PersonEmail (state: active)
- Statusänderung einer bestehenden PersonEmail von "inactive" zu "active"?\ 
  ('gueltig_von', 'gueltig_bis' und das Format der E-Mail Adresse müssen passen)
- Falls eine Änderung am Feld 'email' zulässig ist wird nur wenn sich die email tatsächlich verändert hat
  'last_email_update' aktualisiert. (Diese Regel kann komplett entfallen wenn wir Änderungen am Feld 'email' nicht 
  zulassen sondern nur den Umzug anbieten!)
  
## UMZUG: Änderung einer E-Mail Adresse 
Wird die Hauptemailadresse geändert muss eine Umzug der PersonEmailGruppe(n) und des odoo-user-logins stattfinden.
Dieser könnte in etwa so aussehen:

1. Änderung des Feldes email bei res.partner -> Führt zu der Anlage einer neuen PersonEmail
2. Anlage einer neuen PersonEmail die zur neue Hauptemailadresse wird (status: 'active')
3. Kopie aller (nicht bereits vorhandenen) PersonEmailGruppe(n)\
   WICHTIG: Aktive PersonEmailGruppe(n) (im Status active 
   oder approved) werden mit dem Status 'waiting_for_email_approval' erstellt, und sind daher inaktiv bis die neue 
   E-Mail Adresse bestätigt wird.
4. Aussendung einer DOI E-Mail zur Bestätigung der neuen PersonEmail (Durch FRST oder FSON)
5. Nach dem Klick auf den Bestätigungslink wechselt der Status der neuen PersonEmail von 'active' zu 'approved'!
   Weiters werden alle PersonEmailGruppen im Status "waiting_for_email_approval" auf den status 'active' oder 'approved'
   geändert (je nachdem was in ihrem Feld 'bestaetigt_am_um' und bei dem zugehörigen Gruppenordner für das DOI
   eingestellt ist)
   
Falls es keine relevanten Verknüpfungen gibt kann der Bestätigungsablauf/Umzug auch übersprungen werden.

### E-Mail UMZUG für odoo-login-user und FS-Tokens
Besteht für die Person (res.partner) bereits ein odoo user (Login) muss dieser beim Umzug einer E-Mail Adresse 
berücksichtigt werden. Es muss also 
- geprüft werden ob die neue E-Mail Adresse noch als login verfügbar ist 
- der aktuelle odoo-login gesperrt werden
- alle aktuellen fs-tokens müssen gesperrt werden
 
Sobald die neue E-Mail Adresse bestätigt ist wird
- das login des odoo res.user auf die neue E-Mail geändert
- Die Tokens wieder aktiviert

# Alternative Umsetzung von E-Mail Änderungen
Falls durch das obige Schema (zu viele) ungewollte Umzüge entstehen könnte man auch entscheiden das ein Umzug nur durch
- den Sachbearbeiter in FRST mittels eigens dafür zu programmierenden GUI
- oder bei Änderungen an der e-mail wenn ein User in FSO eingeloggt ist (z.B.: via Token)
- oder einem PersonenMerge in FRST der sich trotz abweichender E-Mails sicher ist die Personen zusammen zu legen
durchgeführt werden.

Änderungen an dem Feld 'email' bei res.partner würden dann zwar zu einer neuen PersonEmail führen diese würde jedoch
nicht automatisch zur neuen Hauptemailadresse werden sofern für die bestehende Hauptemailadresse Gruppenanmeldungen oder
ein odoo-login existieren.

