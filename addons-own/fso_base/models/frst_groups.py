# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class FRSTGruppeState(models.AbstractModel):
    """ Compute the state based on 'gueltig_von' and 'gueltig_bis' Fields

    HINT: Simply overwrite the methods if you need a more complex computation of the state
    """
    _name = "frst.gruppestate"

    state = fields.Selection(selection=[('subscribed', 'Subscribed'),
                                        ('unsubscribed', 'Unsubscribed'),
                                        ('expired', 'Expired')],
                             string="State", readonly=True)

    @api.multi
    def compute_state(self):
        # ATTENTION: Make sure only the field state is written in this method and no other field! (see CRUD)
        mandatory_fields = ('gueltig_von', 'gueltig_bis')
        assert all(hasattr(self, f) for f in mandatory_fields), "Fields 'gueltig_von' and 'gueltig_bis' must exist!"

        for r in self:
            now = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

            # Compute 'steuerung_bit'
            steuerung_bit = True
            if hasattr(r, 'steuerung_bit'):
                steuerung_bit = r.steuerung_bit

            # Compute state
            if r.gueltig_von <= now <= r.gueltig_bis:
                state = 'subscribed' if steuerung_bit else 'unsubscribed'
            else:
                state = 'expired'

            # Write state
            if r.state != state:
                r.write({'state': state})
        return True

    @api.multi
    def compute_all_states(self):
        # ATTENTION: Make sure only the field state is written in this method and no other field! (see CRUD)
        now = fields.datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

        # Search for subscribed groups
        subscribed_domain = [
            ('gueltig_von', '<=', now),
            ('gueltig_bis', '>=', now),
            ('state', 'not in', ('subscribed',))
        ]
        if hasattr(self, 'steuerung_bit'):
            subscribed_domain.append(('steuerung_bit', '=', True))
        subscribed = self.sudo().search(subscribed_domain)
        subscribed.write({'state': 'subscribed'})

        # Search for unsubscribed groups
        unsubscribed_domain = [
            ('gueltig_von', '<=', now),
            ('gueltig_bis', '>=', now),
            ('state', 'not in', ('unsubscribed',))
        ]
        if hasattr(self, 'steuerung_bit'):
            unsubscribed_domain.append(('steuerung_bit', '=', False))
        unsubscribed = self.sudo().search(unsubscribed_domain)
        unsubscribed.write({'state': 'unsubscribed'})

        # Search for expired groups
        expired = self.sudo().search([
            ('state', 'not in', ('expired',)),
            '|',
              ('gueltig_von', '>', now),
              ('gueltig_bis', '<', now),
        ])
        expired.write({'state': 'expired'})
        return True

    @api.model
    def scheduled_compute_all_states(self):
        self.compute_all_states()
        return True

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values, **kwargs):
        values = values or dict()
        res = super(FRSTGruppeState, self).create(values, **kwargs)
        if res and not values.keys() == ['state']:
                res.compute_state()
        return res

    @api.multi
    def write(self, values, **kwargs):
        values = values or dict()
        res = super(FRSTGruppeState, self).write(values, **kwargs)
        if res and not values.keys() == ['state']:
            self.compute_state()
        return res


# Fundraising Studio group folders
# zGruppe are "folders" for groups that determine for what model a zGruppeDetail is valid
class FRSTzGruppe(models.Model):
    _name = "frst.zgruppe"
    _rec_name = "gruppe_lang"

    tabellentyp_id = fields.Selection(selection=[('100100', 'Person'),
                                                 ('100102', 'Adresse'),
                                                 ('100104', 'Kommunikation'),
                                                 ('100106', 'Vertrag'),
                                                 ('100108', 'zVerzeichnis'),
                                                 ('100110', 'Email'),
                                                 ('100112', 'Telefon'),
                                                 ('100114', 'zEvent'),
                                                 ('100116', 'Aktion')],
                                      string="TabellentypID",
                                      help="Select model where Groups in this folder apply",
                                      required=True)

    gruppe_kurz = fields.Char("GruppeKurz", required=True,
                              help="Interne Bezeichnung")
    gruppe_lang = fields.Char("GruppeLang", required=True,
                              help="Anzeige fuer den Kunden und im GUI")
    gui_anzeigen = fields.Boolean("GuiAnzeigen")

    zgruppedetail_ids = fields.One2many(comodel_name="frst.zgruppedetail", inverse_name='zgruppe_id',
                                        string="zGruppeDetail IDS")


# Fundraising Studio groups
class FRSTzGruppeDetail(models.Model):
    _name = "frst.zgruppedetail"
    _rec_name = "gruppe_lang"

    zgruppe_id = fields.Many2one(comodel_name="frst.zgruppe", inverse_name='zgruppedetail_ids',
                                 string="zGruppeID",
                                 required=True, ondelete="cascade")

    gruppe_kurz = fields.Char("GruppeKurz", required=True)
    gruppe_lang = fields.Char("GruppeLang", required=True)
    gui_anzeigen = fields.Boolean("GuiAnzeigen",
                                  help="If set this group is available for this instance")

    # ATTENTION: gueltig_von und gueltig_bis is NOT IN USE for zGruppeDetail and can be removed in the future
    gueltig_von = fields.Date("GültigVon", required=True)   # Not used -> Wird in Sicht integriert als Anlagedatum. Ist derzeit nicht als Anlagedatum gedacht!
    gueltig_bis = fields.Date("GültigBis", required=True)   # Not used

    # PersonGruppe
    frst_persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='zgruppedetail_id',
                                            string="PersonGruppe IDS")

    # PersonEmailGruppe
    frst_personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='zgruppedetail_id',
                                                 string="PersonEmailGruppe IDS")


# PersonGruppe: FRST groups for res.partner
class FRSTPersonGruppe(models.Model):
    _name = "frst.persongruppe"
    _inherit = ["frst.gruppestate"]

    FRST_GRUPPE_TO_CHECKBOX = {
        110493: 'donation_deduction_optout_web',
        128782: 'donation_deduction_disabled',
        20168: 'donation_receipt_web',  # DEPRECATED!
        # TODO: Email Sperrgruppe (11102)
    }

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_persongruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100100')],
                                       required=True, ondelete='cascade')
    partner_id = fields.Many2one(comodel_name="res.partner", inverse_name='persongruppe_ids',
                                 string="Person",
                                 required=True, ondelete='cascade')
    steuerung_bit = fields.Boolean(string="Steuerung Bit")
    gueltig_von = fields.Date("GültigVon", required=True)
    gueltig_bis = fields.Date("GültigBis", required=True)

    @api.model
    def create(self, values, **kwargs):
        res = super(FRSTPersonGruppe, self).create(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            partner = res.mapped('partner_id')
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_persongruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def write(self, values, **kwargs):
        res = super(FRSTPersonGruppe, self).write(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            partner = self.mapped('partner_id')
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_persongruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def unlink(self):
        partner = self.mapped('partner_id')

        res = super(FRSTPersonGruppe, self).unlink()

        # Update res.partner checkboxes
        if res and partner:
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_persongruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res


# Inverse Field for PersonGruppe
class ResPartner(models.Model):
    _inherit = 'res.partner'

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='partner_id',
                                       string="FRST PersonGruppe IDS")

    @api.multi
    def update_personemailgruppe_by_checkbox(self, zgruppedetail_fs_id=None, partner_boolean_field=None):
        assert isinstance(zgruppedetail_fs_id, int), "Attribute 'zgruppedetail_fs_id' missing or no integer!"
        assert isinstance(partner_boolean_field, basestring), "Attribute 'partner_boolean_field' missing or no string!"
        if self:
            assert isinstance(self._fields[partner_boolean_field], fields.Boolean), \
                "Partner has no bolean field '%s'!" % partner_boolean_field

        for r in self:
            main_email = r.frst_personemail_ids.filtered(
                lambda e: e.main_address
            )

            if not main_email:
                logger.info("partner id %s has no main address, "
                            "skipping update_personemailgruppe_by_checkbox"
                            % r.id)
                continue

            # TODO: Instead of three filter do only one for loop
            subscribed = main_email.personemailgruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'subscribed'
            )
            unsubscribed = main_email.personemailgruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'unsubscribed'
            )
            expired = main_email.personemailgruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'expired'
            )

            assert not (subscribed and unsubscribed), "zGruppeDetail (%s) is subscribed and unsubscribed at the " \
                                                      "same time! (partner id %s, frst.personemail id %s)"\
                                                      % (zgruppedetail_fs_id, r.id, main_email.id)

            # CHECKBOX IS SET (True)
            if r[partner_boolean_field] and not subscribed:

                # Enable unsubscribed
                if unsubscribed:
                    if len(unsubscribed) > 1:
                        logger.error("More than one unsubscribed zGruppeDetail (%s) for partner %s"
                                     "frst.personemail id %s" % (zgruppedetail_fs_id, r.id, main_email.id))
                    unsubscribed.sudo().write({'steuerung_bit': True})
                    # Continue with next partner
                    continue

                # Enable expired
                if expired:
                    if len(expired) > 1:
                        logger.warning("More than one expired zGruppeDetail (%s) for partner %s"
                                       "frst.personemail id %s" % (zgruppedetail_fs_id, r.id, main_email.id))

                    expired.sorted(key=lambda person: person.write_date, reverse=True)
                    expired = expired[0]

                    gueltig_von = fields.datetime.strptime(expired.gueltig_von, DEFAULT_SERVER_DATE_FORMAT)
                    if gueltig_von > fields.datetime.now():
                        gueltig_von = fields.datetime.now()
                    gueltig_bis = fields.datetime.strptime(expired.gueltig_bis, DEFAULT_SERVER_DATE_FORMAT)
                    if gueltig_bis < fields.datetime.now():
                        gueltig_bis = fields.date(2099, 12, 31)

                    expired.sudo().write({'gueltig_von': gueltig_von, 'gueltig_bis': gueltig_bis, 'steuerung_bit': True})
                    # Continue with next partner
                    continue

                # Create PersonEmailGruppe
                zgruppedetail = self.env['frst.zgruppedetail'].sudo().search(
                    [('sosync_fs_id', '=', zgruppedetail_fs_id)], limit=1,
                )
                self.env['frst.personemailgruppe'].sudo().create({
                    'zgruppedetail_id': zgruppedetail.id,
                    'personemail_id': main_email.id,
                    'steuerung_bit': True,
                    'gueltig_von': fields.datetime.now(),
                    'gueltig_bis': fields.date(2099, 12, 31),
                })

            # CHECKBOX IS NOT SET (True)
            if not r[partner_boolean_field] and subscribed:
                # ATTENTION: We can not know if we should unsubscribe or expire a group :(
                #            TODO: If we add a field to FRST 'steuerung_bit_erlaubt' we could base our decision on this
                #            TODO: If a group exist already and unsubscribe is allowed we unsubscribe instead of expire!
                subscribed.sudo().write({'gueltig_bis': fields.datetime.now() - timedelta(days=1)})

        return True

    @api.multi
    def update_persongruppe_by_checkbox(self, zgruppedetail_fs_id=None, partner_boolean_field=None):
        assert isinstance(zgruppedetail_fs_id, int), "Attribute 'zgruppedetail_fs_id' missing or no integer!"
        assert isinstance(partner_boolean_field, basestring), "Attribute 'partner_boolean_field' missing or no string!"
        if self:
            assert isinstance(self._fields[partner_boolean_field], fields.Boolean), \
                "Partner has no bolean field '%s'!" % partner_boolean_field

        for r in self:

            # TODO: Instead of three filter do only one for loop
            subscribed = r.persongruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'subscribed'
            )
            unsubscribed = r.persongruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'unsubscribed'
            )
            expired = r.persongruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'expired'
            )

            assert not (subscribed and unsubscribed), "zGruppeDetail (%s) is subscribed and unsubscribed at the " \
                                                      "same time! (partner id %s)" % (zgruppedetail_fs_id, r.id)

            # CHECKBOX IS SET (True)
            if r[partner_boolean_field] and not subscribed:

                # Enable unsubscribed
                if unsubscribed:
                    if len(unsubscribed) > 1:
                        logger.error("More than one unsubscribed zGruppeDetail (%s) for partner %s"
                                     "" % (zgruppedetail_fs_id, r.id))
                    unsubscribed.sudo().write({'steuerung_bit': True})
                    # Continue with next partner
                    continue

                # Enable expired
                if expired:
                    if len(expired) > 1:
                        logger.warning("More than one expired zGruppeDetail (%s) for partner %s"
                                       "" % (zgruppedetail_fs_id, r.id))

                    expired.sorted(key=lambda person: person.write_date, reverse=True)
                    expired = expired[0]

                    gueltig_von = fields.datetime.strptime(expired.gueltig_von, DEFAULT_SERVER_DATE_FORMAT)
                    if gueltig_von > fields.datetime.now():
                        gueltig_von = fields.datetime.now()
                    gueltig_bis = fields.datetime.strptime(expired.gueltig_bis, DEFAULT_SERVER_DATE_FORMAT)
                    if gueltig_bis < fields.datetime.now():
                        gueltig_bis = fields.date(2099, 12, 31)

                    expired.sudo().write({'gueltig_von': gueltig_von, 'gueltig_bis': gueltig_bis, 'steuerung_bit': True})
                    # Continue with next partner
                    continue

                # Create PersonGruppe
                zgruppedetail = self.env['frst.zgruppedetail'].sudo().search(
                    [('sosync_fs_id', '=', zgruppedetail_fs_id)], limit=1,
                )
                self.env['frst.persongruppe'].sudo().create({
                    'zgruppedetail_id': zgruppedetail.id,
                    'partner_id': r.id,
                    'steuerung_bit': True,
                    'gueltig_von': fields.datetime.now(),
                    'gueltig_bis': fields.date(2099, 12, 31),
                })

            # CHECKBOX IS NOT SET (True)
            if not r[partner_boolean_field] and subscribed:
                # ATTENTION: We can not know if we should unsubscribe or expire a group :(
                #            TODO: If we add a field to FRST 'steuerung_bit_erlaubt' we could base our decision on this
                #            TODO: If a group exist already and unsubscribe is allowed we unsubscribe instead of expire!
                subscribed.sudo().write({'gueltig_bis': fields.datetime.now() - timedelta(days=1)})

        return True

    # HINT: This method is triggered in the CRUD Methods of frst.persongruppe
    @api.multi
    def update_checkbox_by_persongruppe(self, zgruppedetail_fs_id=None, partner_boolean_field=None):
        assert isinstance(zgruppedetail_fs_id, int), "Attribute 'zgruppedetail_fs_id' missing or no integer!"
        assert isinstance(partner_boolean_field, basestring), "Attribute 'partner_boolean_field' missing or no string!"
        if self:
            assert isinstance(self._fields[partner_boolean_field], fields.Boolean), \
                "Partner has no bolean field '%s'!" % partner_boolean_field

        for r in self:
            subscribed = r.persongruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'subscribed'
            )

            # Check that no unsubscribed PersonGruppe exists also
            unsubscribed = r.persongruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'unsubscribed'
            )
            assert not (subscribed and unsubscribed), "zGruppeDetail (%s) is subscribed and unsubscribed at the " \
                                                      "same time! (partner id %s)" % (zgruppedetail_fs_id, r.id)

            checkbox_value = True if subscribed else False
            if r[partner_boolean_field] != checkbox_value:
                r.sudo().write({partner_boolean_field: checkbox_value, 'skipp_persongruppe_by_checkbox': True})
        return True

    # HINT: This method is triggered in the CRUD Methods of frst.personemailgruppe
    @api.multi
    def update_checkbox_by_personemailgruppe(self, zgruppedetail_fs_id=None, partner_boolean_field=None):
        assert isinstance(zgruppedetail_fs_id, int), "Attribute 'zgruppedetail_fs_id' missing or no integer!"
        assert isinstance(partner_boolean_field, basestring), "Attribute 'partner_boolean_field' missing or no string!"
        if self:
            assert isinstance(self._fields[partner_boolean_field], fields.Boolean), \
                "Partner has no bolean field '%s'!" % partner_boolean_field

        for r in self:
            main_email = r.frst_personemail_ids.filtered(
                lambda e: e.main_address
            )

            # without a main email address, continue with next row
            if not main_email:
                logger.info("partner id %s has no main address, "
                            "skipping update_checkbox_by_personemailgruppe"
                            % r.id)
                continue

            # with a main email address, check group state
            subscribed = main_email.personemailgruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'subscribed'
            )

            # Check that no unsubscribed PersonEmailGruppe exists also
            unsubscribed = main_email.personemailgruppe_ids.filtered(
                lambda g: g.zgruppedetail_id.sosync_fs_id == zgruppedetail_fs_id and g.state == 'unsubscribed'
            )
            assert not (subscribed and unsubscribed), "zGruppeDetail (%s) is subscribed and unsubscribed at the " \
                                                      "same time! (partner id %s, frst.personemail id %s)"\
                                                      % (zgruppedetail_fs_id, r.id, main_email.id)

            checkbox_value = True if subscribed else False
            if r[partner_boolean_field] != checkbox_value:
                r.sudo().write({partner_boolean_field: checkbox_value, 'skipp_personemailgruppe_by_checkbox': True})
        return True

    @api.model
    def create(self, values, **kwargs):
        values = values or {}
        skipp_persongruppe_by_checkbox = values.pop('skipp_persongruppe_by_checkbox', False)
        skipp_personemailgruppe_by_checkbox = values.pop('skipp_personemailgruppe_by_checkbox', False)

        res = super(ResPartner, self).create(values, **kwargs)

        # Update PersonGruppe by checkboxes
        if res and not skipp_persongruppe_by_checkbox:
            FRST_GRUPPE_TO_CHECKBOX = self.env['frst.persongruppe'].FRST_GRUPPE_TO_CHECKBOX
            for (zgruppedetail_fs_id, partner_boolean_field) in FRST_GRUPPE_TO_CHECKBOX.iteritems():
                res.update_persongruppe_by_checkbox(zgruppedetail_fs_id, partner_boolean_field)

        # Update PersonEmailGruppe by checkboxes
        if res and not skipp_personemailgruppe_by_checkbox:
            FRST_GRUPPE_TO_CHECKBOX = self.env['frst.personemailgruppe'].FRST_GRUPPE_TO_CHECKBOX
            for (zgruppedetail_fs_id, partner_boolean_field) in FRST_GRUPPE_TO_CHECKBOX.iteritems():
                res.update_personemailgruppe_by_checkbox(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def write(self, values, **kwargs):
        values = values or {}
        skipp_persongruppe_by_checkbox = values.pop('skipp_persongruppe_by_checkbox', False)
        skipp_personemailgruppe_by_checkbox = values.pop('skipp_personemailgruppe_by_checkbox', False)

        res = super(ResPartner, self).write(values, **kwargs)

        # Update PersonGruppe by checkboxes
        if res and not skipp_persongruppe_by_checkbox:
            FRST_GRUPPE_TO_CHECKBOX = self.env['frst.persongruppe'].FRST_GRUPPE_TO_CHECKBOX
            for (zgruppedetail_fs_id, partner_boolean_field) in FRST_GRUPPE_TO_CHECKBOX.iteritems():
                self.update_persongruppe_by_checkbox(zgruppedetail_fs_id, partner_boolean_field)

        # Update PersonEmailGruppe by checkboxes
        if res and not skipp_personemailgruppe_by_checkbox:
            FRST_GRUPPE_TO_CHECKBOX = self.env['frst.personemailgruppe'].FRST_GRUPPE_TO_CHECKBOX
            for (zgruppedetail_fs_id, partner_boolean_field) in FRST_GRUPPE_TO_CHECKBOX.iteritems():
                self.update_personemailgruppe_by_checkbox(zgruppedetail_fs_id, partner_boolean_field)

        return res


# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _name = "frst.personemailgruppe"
    _inherit = ["frst.gruppestate"]

    FRST_GRUPPE_TO_CHECKBOX = {
        30104: 'newsletter_web',
    }

    zgruppedetail_id = fields.Many2one(comodel_name="frst.zgruppedetail", inverse_name='frst_personemailgruppe_ids',
                                       string="zGruppeDetail",
                                       domain=[('zgruppe_id.tabellentyp_id', '=', '100110')],
                                       required=True, ondelete='cascade')
    frst_personemail_id = fields.Many2one(comodel_name="frst.personemail", inverse_name='personemailgruppe_ids',
                                          string="FRST PersonEmail",
                                          required=True, ondelete='cascade')
    steuerung_bit = fields.Boolean(string="Steuerung Bit")
    gueltig_von = fields.Date("GültigVon", required=True)
    gueltig_bis = fields.Date("GültigBis", required=True)

    @api.model
    def create(self, values, **kwargs):
        res = super(FRSTPersonEmailGruppe, self).create(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            email = res.mapped('frst_personemail_id')

            if email.main_address:
                partner = email.mapped('partner_id')
                for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                    partner.update_checkbox_by_personemailgruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def write(self, values, **kwargs):
        res = super(FRSTPersonEmailGruppe, self).write(values, **kwargs)

        # Update res.partner checkboxes
        if res:
            email = self.mapped('frst_personemail_id')

            if email.main_address:
                partner = email.mapped('partner_id')
                for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                    partner.update_checkbox_by_personemailgruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res

    @api.multi
    def unlink(self):
        email = self.mapped('frst_personemail_id')

        if email:
            partner = email.mapped('partner_id')

        res = super(FRSTPersonEmailGruppe, self).unlink()

        # Update res.partner checkboxes
        if email and res and partner:
            for (zgruppedetail_fs_id, partner_boolean_field) in self.FRST_GRUPPE_TO_CHECKBOX.iteritems():
                partner.update_checkbox_by_personemailgruppe(zgruppedetail_fs_id, partner_boolean_field)

        return res


# Inverse Field for PersonEmailGruppe
class FRSTPersonEmail(models.Model):
    _inherit = "frst.personemail"

    personemailgruppe_ids = fields.One2many(comodel_name="frst.personemailgruppe", inverse_name='frst_personemail_id',
                                            string="FRST PersonEmailGruppe IDS")
