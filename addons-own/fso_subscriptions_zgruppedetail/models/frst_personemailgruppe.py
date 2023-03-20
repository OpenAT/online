# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

# PersonEmailGruppe: FRST groups for email addresses
class FRSTPersonEmailGruppe(models.Model):
    _inherit = "frst.personemailgruppe"

    mass_mailing_list_contact_ids = fields.One2many(string="Mailing List Contact",
                                                    comodel_name="mail.mass_mailing.contact",
                                                    inverse_name="personemailgruppe_id",
                                                    readonly=True)

    # Create, Link and Update Mass Mailing List Contacts
    @api.multi
    def compute_mass_mailing_list_contact_ids(self, vals):
        mlists = self.env['mail.mass_mailing.list'].sudo().search([('zgruppedetail_id', '!=', False)])
        mlistcontacts = self.env['mail.mass_mailing.contact']
        mlists_zgroups = mlists.mapped('zgruppedetail_id')

        # Only process PersonEmailGroups with a zGruppeDetail used in a mailing list
        peg_records = self.filtered(lambda r: r.zgruppedetail_id in mlists_zgroups)

        for peg in peg_records:
            peg_opt_out = True if peg.state in ('unsubscribed', 'expired') else False
            zgruppedetail = peg.zgruppedetail_id

            # Find the mailing list where this zGruppeDetail is set
            mlist = mlists.filtered(lambda r: r.zgruppedetail_id == zgruppedetail)
            assert len(mlist) == 1, "More than one mailing list found for zGruppeDetail %s" % zgruppedetail.id

            # Search for existing mailing list contact
            # ----------------------------------------
            lc = mlistcontacts.search([('list_id', '=', mlist.id), ('personemail_id', '=', peg.frst_personemail_id.id)])
            assert len(lc) <= 1, _("More than one list contact found for the same PersonEmail in one mailing list! %s"
                                   ) % lc.ids

            # Suppress the compute_person_email_gruppe method for mailing list contact create or write
            # ----------------------------------------------------------------------------------------
            lc_skipp = lc.sudo().with_context(skipp_compute_person_email_gruppe=True)

            # Create a mailing list contact
            # -----------------------------
            if not lc_skipp:
                lc_skipp.create({'list_id': mlist.id,
                                 'personemailgruppe_id': peg.id,
                                 'personemail_id': peg.frst_personemail_id.id,
                                 #'zgruppedetail_id': zgruppedetail.id,
                                 'firstname': peg.frst_personemail_id.partner_id.firstname,
                                 'lastname': peg.frst_personemail_id.partner_id.lastname,
                                 'email': peg.frst_personemail_id.email,
                                 'opt_out': peg_opt_out,
                                 'bestaetigt_am_um': peg.bestaetigt_am_um,
                                 'bestaetigt_typ': peg.bestaetigt_typ,
                                 'bestaetigt_herkunft': peg.bestaetigt_herkunft})

            # Update the mailing list contact
            # -------------------------------
            else:
                # Transfer opt_out
                if peg_opt_out != lc_skipp.opt_out:
                    lc_skipp.write({'opt_out': peg_opt_out})

                # Transfer 'bestaetigt_am_um'
                if 'bestaetigt_am_um' in vals:
                    lc_skipp.write(
                        {'bestaetigt_am_um': vals['bestaetigt_am_um'],
                         'bestaetigt_typ': vals.get('bestaetigt_typ', peg.bestaetigt_typ),
                         'bestaetigt_herkunft': vals.get('bestaetigt_herkunft', peg.bestaetigt_herkunft)})
                elif peg.bestaetigt_am_um and not lc_skipp.bestaetigt_am_um:
                    lc_skipp.write(
                        {'bestaetigt_am_um': peg.bestaetigt_am_um,
                         'bestaetigt_typ': peg.bestaetigt_typ,
                         'bestaetigt_herkunft': peg.bestaetigt_herkunft})
                elif not peg.bestaetigt_am_um and lc_skipp.bestaetigt_am_um:
                    peg.sudo().with_context(skipp_compute_mass_mailing_list_contact_ids=True).write(
                        {'bestaetigt_am_um': lc_skipp.bestaetigt_am_um,
                         'bestaetigt_typ': lc_skipp.bestaetigt_typ,
                         'bestaetigt_herkunft': lc_skipp.bestaetigt_herkunft})

                # Link the PersonEmailGruppe to the mailing list contact
                if lc_skipp.personemailgruppe_id:
                    assert peg.id == lc_skipp.personemailgruppe_id.id, _(
                        "A different PersonEmailGruppe %s is already assigned to the list contact %s! "
                        "Could not assign PersonEmailGruppe %s"
                        "") % (lc_skipp.personemailgruppe_id.id, lc_skipp.id, peg.id)
                else:
                    lc_skipp.write({'personemailgruppe_id': peg.id})

    @api.model
    def create(self, vals):
        res = super(FRSTPersonEmailGruppe, self).create(vals)

        if not self.env.context.get('skipp_compute_mass_mailing_list_contact_ids', False):
            if res and 'mass_mailing_list_contact_ids' not in vals:
                res.compute_mass_mailing_list_contact_ids(vals=vals)

        return res

    @api.multi
    def write(self, vals):
        res = super(FRSTPersonEmailGruppe, self).write(vals)

        if not self.env.context.get('skipp_compute_mass_mailing_list_contact_ids', False):
            if res and 'mass_mailing_list_contact_ids' not in vals:
                self.compute_mass_mailing_list_contact_ids(vals=vals)

        return res

    # HINT: Currently we will NOT delete a PersonEmailGruppe if the List Contact gets deleted. But we delete the List
    #       contact when the PersonEmailGruppe gets deleted!
    @api.multi
    def unlink(self):

        # Delete related mail list contacts first
        for peg in self:
            if peg.mass_mailing_list_contact_ids:
                peg.mass_mailing_list_contact_ids.unlink()

        res = super(FRSTPersonEmailGruppe, self).unlink()
        return res
