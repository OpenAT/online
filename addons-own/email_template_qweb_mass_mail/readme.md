# Links and Info

Intresting external resources
- [Mail Chimp Templates on github](https://github.com/mailchimp/Email-Blueprints)
- [HTML Email Check and Validation Tool](https://www.htmlemailcheck.com/)
- [E-Mail Client Market Share](http://emailclientmarketshare.com/)
- [Litmus Email Analytics](https://litmus.com/email-analytics)
- [CSS support by e-mail agent](https://www.campaignmonitor.com/css)
- [Mail-Chimp CSS inliner tool](https://templates.mailchimp.com/resources/inline-css/)
- [Python CSS inliner tool: premailer on pypi](https://pypi.python.org/pypi/premailer)
- [Python CSS inliner tool: premailer on Github](https://github.com/peterbe/premailer)

Other possible e-mail editors
- [GrapeJS for E-Mails (OS & free, a bit technical)](http://grapesjs.com/)
- [unlayer / react-email-editor (OS & free)](https://github.com/unlayer/react-email-editor)
- [mosaico (OS & free, low developement)](https://mosaico.io/)
- [Bee Pro embedded (SAAS, $100/Mon + $2/mon/user)](https://beefree.io/bee-plugin/)
- [MailChimp (Paid & not a standalone editor)]()
- [ory (not e-mail specific)](https://github.com/ory/editor)
- [Stamplia (website down)]()

# Odoo email editor
The odoo email editor is based on Jinja2 (not Qweb in odoo 8) and can be extended by snippets. Templates as a starting
point are supported.

#### Pros:
- Free and Open Source
- E-Mail editor works the same as the website editor
    - Easier to learn and train for us and the customer
    - Only one training for widgets and e-mails
    - HTML-Link tool is the same
- Simple drag and drop WYSIWYG editor
- User authorization and single sign on very easy by FS-Token or already existing studio user
- Serves as CDN (Content Delivery Network) for images and files out of the box
- Programming and maintenance knowledge is already available
- Setup, Backup and service monitoring is already done
    - Setup of external customer domains partially already available
    - Lots of information for e-mail template placeholders are already available (company data)
- No external service involved (DSVGO) (all data inhouse)
- Templating engine is very close to pure HTML
- All development adds to FS-Online

#### Cons:
- Good base e-mail templates and snippets must be created (e.g. based on mailchimp)(approx 2 weeks)
- E-Mail templates will not be auto-updated by an external provider (this may be the same for most saas software too)
- Real-Time mobile and tablet popup preview must be coded (approx 2 days)
- No image crop and rotate build in (approx 4 days inhouse or 1 day by external java dev)
- Style changes may require snippet changes also (except *premailer* works well)
- No hierarchical templating (tcall) for jinja2 templates

## Addons involved

- [Anton Chepurov extension for mass mail to work with email_template_qweb](https://github.com/a0c)
- [OCA/social/email_template_qweb](https://github.com/OCA/social/tree/8.0/email_template_qweb)
- [OCA/social/mail_inline_css from odoo v10](https://github.com/OCA/social/tree/10.0/mail_inline_css)

### Odoo native
- mass_mailing
- website_mail

### OCA / social
- email_template_qweb

### addons_own
- email_template_qweb_mass_mail


# Basic Info (DEV)
New E-Mail templates can be created in the model **email.template** with **Mass Mailing Contact** 
(mail.mass_mailing.contact) as the model_id. Those email templates will than be listed by the addon website_mail.

New **Snippets** for e-mail templates can be created in the the template qweb view with the view id 
**email_designer_snippets** in the addon **website_mail**.

# TODO

To make the odoo e-mail editor working as the FRST e-mail template editor we would need to:

- Create a base e-mail template based on the mail chimp templates
- Create some basic snippets for the content based on the mail chimp templates
- Implement a CSS to Inline CSS tool in odoo
- Make sure Links (and button Links) use inline CSS instead of bootstrap classes
- Make sure the correct base URLs are used for links
- Allow to set alt text for images
- Hide website menu and footer

Optional / nice to have

- Rotate and crop images
- Auto Resize images
- Force the alt text for images
- Sort templates in a Folder like structure
- Sort created (mass) e-mails in a folder like structure
- Extend the "html-link" editor to
    - Show only relevant results/pages
    - Easily create Links with pre authorization (FSO Token Links)
- Hide colors and styles for text that are not needed or wanted
- Replace colors and font-sizes for text with the corporate design ones
