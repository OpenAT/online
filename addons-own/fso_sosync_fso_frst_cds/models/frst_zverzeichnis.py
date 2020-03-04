# -*- coding: utf-8 -*-

from openerp import models, fields


class FRSTzVerzeichnisSosync(models.Model):
    _name = 'frst.zverzeichnis'
    _inherit = ['frst.zverzeichnis', 'base.sosync']

    verzeichnisname = fields.Char(sosync="True")
    verzeichnislang = fields.Char(sosync="True")
    verzeichniskuerzel = fields.Char(sosync="True")
    bemerkung = fields.Text(sosync="True")

    parent_id = fields.Many2one(sosync="True")
    # child_ids - do not track

    verzeichnistyp_id = fields.Boolean(sosync="True")
    bezeichnungstyp_id = fields.Selection(sosync="True")

    anlagedatum = fields.Date(sosync="True")

    startdatum = fields.Date(sosync="True")
    endedatum = fields.Date(sosync="True")

    verantwortlicher_benutzer = fields.Char(sosync="True")
    fibukontonummer = fields.Char(sosync="True")
    uebersteigendebeitraegeprojahraufspendenzverzeichnisid = fields.Integer(sosync="True")
    cdsdokument = fields.Char(sosync="True")
    xbankverbindungidfuereinzugsvertraege = fields.Integer(sosync="True")

    # Sync deprecated fields anyway
    verwendungalszmarketingid = fields.Boolean(sosync="True")
    sorterinhierarchie = fields.Integer(sosync="True")
    organisationseinheit = fields.Char(sosync="True")
