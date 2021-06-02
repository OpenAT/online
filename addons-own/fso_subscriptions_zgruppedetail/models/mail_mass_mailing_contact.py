# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools import SUPERUSER_ID, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
import datetime

import logging
logger = logging.getLogger(__name__)


class MailMassMailingContact(models.Model):
    _inherit = "mail.mass_mailing.contact"

    # HINT: Currently we will NOT delete a PersonEmailGruppe if the List Contact gets deleted. But we delete the List
    #       contact when the PersonEmailGruppe gets deleted!
    personemailgruppe_id = fields.Many2one(string="PersonEmailGruppe",
                                           comodel_name="frst.personemailgruppe",
                                           index=True,
                                           readonly=True, ondelete="set null")

    @api.multi
    def compute_person_email_gruppe(self, vals):
        vals = vals if vals else {}
        # HINT: lc = Mail List Contact
        for lc in self:
            zgruppedetail = lc.list_id.zgruppedetail_id

            if not zgruppedetail:
                if lc.personemailgruppe_id:
                    lc.with_context(skipp_compute_person_email_gruppe=True).write({'personemailgruppe_id': False})
                    continue

            if zgruppedetail:
                # Find existing PersonEmailGruppe(n) for the PersonEmail and zGruppeDetail
                # ------------------------------------------------------------------------
                # ATTENTION: We skipp the inverse computation of compute_mass_mailing_list_contact_ids!
                pegroup_obj = self.env['frst.personemailgruppe'].sudo().with_context(
                    skipp_compute_mass_mailing_list_contact_ids=True)

                pegroup = pegroup_obj.search([('frst_personemail_id', '=', lc.personemail_id.id),
                                              ('zgruppedetail_id', '=', zgruppedetail.id)])
                assert len(pegroup) <= 1, _(
                    "zGruppeDetail %s is assigned multiple times to PersonEmail %s"
                    "") % (zgruppedetail.id, lc.personemail_id.id)

                # Create the pegroup if none was found
                # ------------------------------------
                if not pegroup:
                    pegroup_vals = {'frst_personemail_id': lc.personemail_id.id,
                                    'zgruppedetail_id': zgruppedetail.id,
                                    'bestaetigt_am_um': lc.bestaetigt_am_um,
                                    'bestaetigt_typ': lc.bestaetigt_typ,
                                    'bestaetigt_herkunft': lc.bestaetigt_herkunft}
                    # ATTENTION: It would be more precise to set 'steuerung_bit': False but since Fundraising
                    #            Studio is inconsistent in this respect we simply do the same than FRST when
                    #            someone clicked on the 'abmelden' link in an email
                    #            Currently there is no explicit opt_out in Fundraising Studio!
                    if lc.opt_out:
                        pegroup_vals.update(
                            {'gueltig_von': datetime.datetime.now() - datetime.timedelta(days=1),
                             'gueltig_bis': datetime.datetime.now() - datetime.timedelta(days=1)})
                    pegroup = pegroup_obj.create(pegroup_vals)

                # Update the pegroup fields by the list contact fields to match the state
                # -----------------------------------------------------------------------
                else:

                    # Transfer opt_out
                    if lc.opt_out and pegroup.state not in ('unsubscribed', 'expired'):
                        # ATTENTION: It would be more precise to set 'steuerung_bit': False but since Fundraising
                        #            Studio is inconsistent in this respect we simply do the same than FRST when
                        #            someone clicked on the 'abmelden' link in an email
                        #            Currently there is no explicit opt_out in Fundraising Studio!
                        pegroup.write(
                            {'gueltig_bis': datetime.datetime.now() - datetime.timedelta(days=1)})
                    if not lc.opt_out and pegroup.state in ('unsubscribed', 'expired'):
                        pegroup.write(
                            {'gueltig_von': datetime.datetime.now() - datetime.timedelta(days=1),
                             'gueltig_bis': datetime.date(2099, 12, 31),
                             'steuerung_bit': True})

                    # Transfer 'bestaetigt_am_um'
                    if 'bestaetigt_am_um' in vals:
                        pegroup.write({'bestaetigt_am_um': vals['bestaetigt_am_um'],
                                       'bestaetigt_typ': vals.get('bestaetigt_typ', lc.bestaetigt_typ),
                                       'bestaetigt_herkunft': vals.get('bestaetigt_herkunft',
                                                                       lc.bestaetigt_herkunft)})
                    elif lc.bestaetigt_am_um and not pegroup.bestaetigt_am_um:
                        pegroup.write({'bestaetigt_am_um': lc.bestaetigt_am_um,
                                       'bestaetigt_typ': lc.bestaetigt_typ,
                                       'bestaetigt_herkunft': lc.bestaetigt_herkunft})
                    elif pegroup.bestaetigt_am_um and not lc.bestaetigt_am_um:
                        lc.with_context(skipp_compute_person_email_gruppe=True).write(
                            {'bestaetigt_am_um': pegroup.bestaetigt_am_um,
                             'bestaetigt_typ': pegroup.bestaetigt_typ,
                             'bestaetigt_herkunft': pegroup.bestaetigt_herkunft})

                # Assign the pegroup to the list contact field personemailgruppe_id
                # -----------------------------------------------------------------
                if lc.personemailgruppe_id:
                    assert lc.personemailgruppe_id.id == pegroup.id, _(
                        "A different PersonEmailGruppe %s is already assigned to the list contact %s! "
                        "Could not assing PersonEmailGruppe %s") % (lc.personemailgruppe_id.id, lc.id, pegroup.id)
                # Assign the pegroup to the list contact field personemailgruppe_id
                else:
                    lc.with_context(skipp_compute_person_email_gruppe=True).write({'personemailgruppe_id': pegroup.id})

    @api.model
    def create(self, vals):
        res = super(MailMassMailingContact, self).create(vals)

        if not self.env.context.get('skipp_compute_person_email_gruppe', False):
            if res and 'personemailgruppe_id' not in vals:
                res.compute_person_email_gruppe(vals=vals)

        return res

    @api.multi
    def write(self, vals):
        res = super(MailMassMailingContact, self).write(vals)

        if not self.env.context.get('skipp_compute_person_email_gruppe', False):
            if res and 'personemailgruppe_id' not in vals:
                self.compute_person_email_gruppe(vals=vals)

        return res

    # HINT: Currently we will NOT delete a PersonEmailGruppe if the List Contact gets deleted. But we delete the List
    #       contact when the PersonEmailGruppe gets deleted!
    # TODO: unlink()
