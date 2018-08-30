# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    persongruppe_ids = fields.One2many(comodel_name="frst.persongruppe", inverse_name='partner_id',
                                       string="FRST PersonGruppe IDS")

    frst_personemail_ids = fields.One2many(comodel_name="frst.personemail", inverse_name='partner_id',
                                           string="FRST PersonEmail IDS")

    main_personemail_id = fields.Many2one(comodel_name="frst.personemail",
                                       string="Main Email", compute="_compute_main_personemail_id")

    @api.depends('frst_personemail_ids.main_address')
    @api.multi
    def _compute_main_personemail_id(self):
        for r in self:
            main_address = r.frst_personemail_ids.filtered(lambda m: m.main_address)
            if main_address:
                assert len(main_address) == 1, "More than one main e-mail address for partner %s" % r.id
            r.main_personemail = main_address.id if main_address else False

    # -----------
    # PersonEmail
    # -----------
    @api.multi
    def update_personemail(self):
        """ Creates, activates or deactivates frst.personemail based on field 'email' of the res.partner

        :return: boolean
        """
        for r in self:
            if r.email:
                partnermail_exits = r.frst_personemail_ids.filtered(lambda m: m.email == r.email)

                # Activate PartnerEmail
                if partnermail_exits:
                    # Do nothing if more than one email was found which is considered as an error
                    # HINT: This should be fixed automatically by Fundraising Studio in a night run
                    #       (FRST merges same mail addresses per partner)
                    if len(partnermail_exits) > 1:
                        logger.error("More than one PartnerEmail %s found for partner with id %s"
                                     "" % (r.id, partnermail_exits[0].email))
                        continue

                    # Make sure this PartnerMail is the main_address
                    if not partnermail_exits.main_address:
                        partnermail_exits.write({'email': r.email})

                # Create PartnerEmail
                else:
                    self.env['frst.personemail'].create({'email': r.email, 'partner_id': r.id})

            # Deactivate PartnerEmail
            else:
                # Deactivate only the main_address for this partner
                # HINT: This was discussed with Martin and Rufus and is considered as the best 'solution' for now
                main_address = r.frst_personemail_ids.filtered(lambda m: m.main_address)
                if main_address:
                    yesterday = fields.datetime.now() - timedelta(days=1)
                    main_address.write({'gueltig_bis': yesterday})

    # -----------------
    # PersonEmailGruppe
    # -----------------
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
                r.write({partner_boolean_field: False, 'skipp_personemailgruppe_by_checkbox': True})
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
                    'frst_personemail_id': main_email.id,
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

    # ------------
    # PersonGruppe
    # ------------
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
                if not zgruppedetail:
                    logger.error('zgruppedetail (ID %s) is missing in the system!' % zgruppedetail_fs_id)
                    # Continue with next partner
                    continue
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

    # ----
    # CRUD
    # ----
    @api.model
    def create(self, values, **kwargs):
        values = values or {}
        skipp_persongruppe_by_checkbox = values.pop('skipp_persongruppe_by_checkbox', False)
        skipp_personemailgruppe_by_checkbox = values.pop('skipp_personemailgruppe_by_checkbox', False)

        res = super(ResPartner, self).create(values, **kwargs)

        # Create a PersonEmail
        email = values.get('email', False)
        if res and email:
            res.env['frst.personemail'].create({'email': email, 'partner_id': res.id})

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

        # Update or create a PersonEmail
        if res and 'email' in values:
            self.update_personemail()

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
