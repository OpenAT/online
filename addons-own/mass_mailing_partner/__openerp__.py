# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "mass_mailing_partner V2",
    'summary': "mass_mailing_partner link mail.mass_mass_mailing.contacts to frst.personeamil records if set in list",
    'description': """
A mail.mass_mailing.contact record is basically only an e-mail assigned to an list (subscription) which
is not related to any other record by default. Therefore a mailing list is just a "list of e-mail 
subscriptions". This addon connects a mail.mass_mailing.contact record (= list subscription = e-mail) to a 
FRST e-mail of a partner which is a frst.personemail record if the "partner_mandatory" boolean field is set 
in the related mailing list (mail.mass_mailing.list).

We use an existing frst.personemail record if exactly one can be found for the email of the list contact at contact creation. 
If none or more than one are found we create a new Partner and a new PersonEmail.

You are able to link a specific frst.personemail record even if there exists multiple records for the email
by the gui or by an xmlrpc request as long as the emails of the frst.personemail record and the 
mail.mass_mailing.contact record match.

HINT: The E-Mail is the only indicator to which res.partner (PersonEmail) a list contact belongs. Therefore it
      can not be allowed to change the email after list contact creation if linked to a partner (PersonEmail).

Some Basic Rules to avoid hijacking of data:
  - 'email' field of a frst.personemail record can not be changed
  - list contact 'email' can not be changed after linked to a PersonEmail
  - 'personemail_id' will be auto-linked and must be set if "partner_mandatory" is set at the mailing list
  - we do NOT transfer person related data from the list contact to the linked res.partner except when a new partner 
    is created
  - If a public-user (belongs to base.group_public) is logged in, the PersonEmail that will be created always belongs to the 
    res.partner of the logged in public user

SECURITY:
---------
We allow public user to create and write mailing list contacts if the partner of the linked personemail matches the partner
of the logged in user. To achieve this we gave full access to the base.group_public to the list contact model but restrict (filter)
the records by ir.rule records. The same applies to personeamil - check the access_rules.xml and ir.model.access.csv for more details.

    """,
    "version": "8.0.3.0.0",
    "author": "Michael Karrer",
    "license": "AGPL-3",
    "category": "Marketing",
    "depends": [
        'mass_mailing',
        'fso_frst_personemail',
        'mass_mail_contact_firstname',
        'partner_firstname_lastname',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/access_rules.xml',
        'views/mail_mail_statistics_view.xml',
        'views/mail_mass_mailing_contact_view.xml',
        'views/mail_mass_mailing_view.xml',
        'views/res_partner_view.xml',
        'views/frst_personemail.xml',
        'wizard/partner_mail_list_wizard.xml',
    ],
    "installable": True,
}
