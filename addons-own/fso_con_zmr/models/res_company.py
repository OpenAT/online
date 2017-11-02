# -*- coding: utf-8 -*-
import os
import errno
from os.path import join as pj
from openerp import api, models, fields
from openerp.tools import config
import logging
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class CompanyAustrianZMRSettings(models.Model):
    _inherit = 'res.company'

    # FIELDS
    BPKRequestIDS = fields.One2many(comodel_name="res.partner.bpk", inverse_name="BPKRequestCompanyID",
                                    string="BPK Requests")
    fa_donation_report_ids = fields.One2many(comodel_name="res.partner.fa_donation_report",
                                             inverse_name="bpk_company_id",
                                             string="Donation Reports")

    # Basic Settings
    stammzahl = fields.Char(string="Firmenbuch-/ Vereinsregisternummer", help='Stammzahl e.g.: XZVR-123456789')

    # PVPToken userPrincipal
    pvpToken_userId = fields.Char(string="User ID (userId)")
    pvpToken_cn = fields.Char(string="Common Name (cn)")
    pvpToken_gvOuId = fields.Char(string="Request Organisation (gvOuId)")
    pvpToken_ou = fields.Char(string="Request Person (ou)")

    # ZMR Requests SSL Zertifikate
    # http://www.ridingbytes.com/2016/01/02/odoo-remember-the-filename-of-binary-files/
    pvpToken_crt_pem = fields.Binary(string="Certificate (PEM)")
    pvpToken_crt_pem_filename = fields.Char(string="Certificate Name", help="crt_pem")
    pvpToken_crt_pem_path = fields.Char(string="Certificate Path",
                                        compute='_certs_to_file', compute_sudo=True, store=True, readonly=True)

    pvpToken_prvkey_pem = fields.Binary(string="Private Key (PEM)")
    pvpToken_prvkey_pem_filename = fields.Char(string="Private Key Name", help="prvkey_pem without password!")
    pvpToken_prvkey_pem_path = fields.Char(string="Private Key Path",
                                           compute='_certs_to_file', compute_sudo=True, store=True, readonly=True)
    # Get BPK request URLS
    BPKRequestURL = fields.Selection(selection=[('https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR',
                                                 'Test: https://pvawp.bmi.gv.at/at.gv.bmi.szrsrv-b/services/SZR'),
                                                ('https://pvawp.bmi.gv.at/bmi.gv.at/soap/SZ2Services/services/SZR',
                                                 'Live: https://pvawp.bmi.gv.at/bmi.gv.at/soap/SZ2Services/services/SZR'),
                                                ],
                                     string="GetBPK Request URL",
                                     default="https://pvawp.bmi.gv.at/bmi.gv.at/soap/SZ2Services/services/SZR")
    # BPK-Request Status messages
    bpk_found = fields.Text(string="BPK Person-Found Message", translate=True)
    bpk_not_found = fields.Text(string="BPK No-Person-Matched Message", translate=True)
    bpk_multiple_found = fields.Text(string="BPK Multiple-Person-Matched Message", translate=True)
    bpk_zmr_service_error = fields.Text(string="BPK ZMR-Service-Error Message", translate=True)

    # Austrian Finanz Online Webservice Session-Login Data
    # https://www.bmf.gv.at/egovernment/fon/fuer-softwarehersteller/softwarehersteller-funktionen.html#Webservices
    fa_tid = fields.Char(string="Teilnehmer Identifikation (tid)")
    fa_benid = fields.Char(string="Webservicebenutzer ID (benid)")
    fa_pin = fields.Char(string="Webservicebenutzer Pin (pin)")
    fa_herstellerid = fields.Char(string="UID-Nummer des Softwareherstellers (herstellerid)")

    # Finanz Online Donation Report Settings (Spendenmeldung)
    fa_dr_url = fields.Selection(selection=[('https://test', 'Test: https://test'),
                                            ('https://production', 'Live: https://production')],
                                 string="Spendenmeldung URL")
    fa_dr_type = fields.Selection(string="Spendenmeldung Uebermitllungstyp",
                                  selection=[('KK', 'Einrichtung Kunst und Kultur (gem. § 4a Abs 2 Z 5 EStG)'),
                                             ('SO', 'Karitative Einrichtungen (gem § 4a Abs 2 Z3 lit a bis c EStG)'),
                                             ('FW', 'Wissenschaftseinrichtungen (gem. 4a Abs 2Z 1 EStG)'),
                                             ('NT', 'Naturschutz und Tierheime (gem § 4a Abs 2 Z 3 lit d und e EStG)'),
                                             ('SN', 'Sammeleinrichtungen Naturschutz (gem § 4a Abs 2 Z 3 lit d und e EStG)'),
                                             ('SG', 'gemeinnützige Stiftungen (§ 4b EStG 1988, hinsichtlich Spenden)'),
                                             ('UN', 'Universitätetn, Kunsthochschulen, Akademie der bildenden Künste (inkl. Fakultäten, Instituteund besondere Einrichtungen, § 4a Abs 3 Z 1 EStG)'),
                                             ('MÖ', 'Museen von Körperschaften öffentlichen Rechts (§ 4a Abs 4 lit b EStG)'),
                                             ('MP', 'Privatmuseen mit überregionaler Bedeutung (§ 4a Abs 4 lit b EStG)'),
                                             ('FF', 'Freiwillige Feuerwehren ( § 4a Abs 6 EStG) und Landesfeuerwehrverbände (§ 4a Abs 6 EStG)'),
                                             ('KR', 'Kirchen und Religionsgesellschaften mit verpflichtenden Beiträgen (§ 18 Abs 1 Z 5 EStG)'),
                                             ('PA', 'Pensionsversicherungsanstalten und Versorgungseinrichtungen (§ 18 Abs 1 Z 1a EStG)'),
                                             ('SE', 'Behindertensportdachverbände, Internationale Anti-Korruptions-Akademie, Diplomatische Akademie (§ 4a Abs 4 EStG)'),
                                             ('ZG', 'gemeinnützige Stiftungen (§ 4b EStG, hinsichtlich Zuwendungen zur Vermögensausstattung)')],
                                  )

    # Action to store certificate files to data dir because request.Session(cert=()) needs file paths
    # https://www.odoo.com/de_DE/forum/hilfe-1/question/
    #     is-there-a-way-to-get-the-location-to-your-odoo-and-to-create-new-files-in-your-custom-module-89677
    @api.depends('pvpToken_crt_pem', 'pvpToken_prvkey_pem')
    def _certs_to_file(self):
        # http://stackoverflow.com/questions/21458155/get-file-path-from-binary-data
        assert config['data_dir'], "config['data_dir'] missing!"
        assert self.env.cr.dbname, "self.env.cr.dbname missing!"
        assert self.env.user.company_id.id, "self.env.user.company_id.id missing!"
        crt_dir = pj(config['data_dir'], "filestore", self.env.cr.dbname,
                     "fso_con_zmr", "company_"+str(self.env.user.company_id.id))
        if not os.path.exists(crt_dir):
            try:
                os.makedirs(crt_dir)
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise
        for rec in self:
            if rec.pvpToken_crt_pem:
                crt_pem_file = pj(crt_dir, rec.pvpToken_crt_pem_filename)
                with open(crt_pem_file, 'w') as f:
                    f.write(rec.pvpToken_crt_pem.decode('base64'))
                # Write path to field
                rec.pvpToken_crt_pem_path = crt_pem_file
            if rec.pvpToken_prvkey_pem:
                prvkey_pem_file = pj(crt_dir, rec.pvpToken_prvkey_pem_filename)
                with open(prvkey_pem_file, 'w') as f:
                    f.write(rec.pvpToken_prvkey_pem.decode('base64'))
                # Write path to field
                rec.pvpToken_prvkey_pem_path = prvkey_pem_file

    # TODO: on deletion of a company delete all related res.partner.bpk records
