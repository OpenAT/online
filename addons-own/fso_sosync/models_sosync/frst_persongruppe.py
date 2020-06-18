# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class FRSTPersonGruppeSosync(models.Model):
    _name = "frst.persongruppe"
    _inherit = ["frst.persongruppe", "base.sosync"]

    zgruppedetail_id = fields.Many2one(sosync="True")
    partner_id = fields.Many2one(sosync="True")

    # From abstract model frst.gruppestate
    state = fields.Selection(sosync="fson-to-frst")

    steuerung_bit = fields.Boolean(sosync="True")
    gueltig_von = fields.Date(sosync="True")
    gueltig_bis = fields.Date(sosync="True")
    bestaetigt_am_um = fields.Datetime(sosync="True")
    bestaetigt_typ = fields.Selection(sosync="True")
    bestaetigt_herkunft = fields.Char(sosync="True")

    # CDS Link
    frst_zverzeichnis_id = fields.Many2one(sosync="True")
