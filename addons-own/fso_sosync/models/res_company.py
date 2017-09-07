# -*- coding: utf-'8' "-*-"
from openerp import models, fields


class ResCompanySosync(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "base.sosync"]

    # FS: dbo.xBPKAccount

    # RELATED FIELDS
    # bank_ids = fields.One2many(sosync="True")              # Company Bank Accounts
    # BPKRequestIDS = fields.One2many(sosync="True")         # BPK Requests
    # child_ids = fields..One2many(sosync="True")            # Child companies
    # parent_id = fields.Many2one(sosync="True")             # Parent Company
    # user_ids = fields.Many2one(sosync="True")              # Accepted Users (Users allowed to use this comp.)
    #country_id = fields.Many2one(sosync="True")
    #state_id = fields.Many2one(sosync="True")
    #partner_id = fields.Many2one(sosync="True")              # res.partner of this company

    # -----------------------------------------------------------------------------------------------------------------

    # Standard fields
    name = fields.Char(sosync="True")
    #email = fields.Char(sosync="True")
    #phone = fields.Char(sosync="True")
    #street = fields.Char(sosync="True")
    #street2 = fields.Char(sosync="True")
    #tax_calculation_rounding_method = fields.Selection(sosync="True")

    # -----------------------------------------------------------------------------------------------------------------

    # FS-Online fields (e.g.: from fso_base)
    #instance_id = fields.Char(sosync="True")
    #instance_base_port = fields.Char(sosync="True")

    # BPK / ZMR
    #stammzahl = fields.Char(sosync="True")

    # PVPToken userPrincipal
    #pvpToken_userId = fields.Char(sosync="True")
    #pvpToken_cn = fields.Char(sosync="True")
    #pvpToken_gvOuId = fields.Char(sosync="True")
    #pvpToken_ou = fields.Char(sosync="True")

    # ZMR Requests SSL Zertifikate
    #pvpToken_crt_pem = fields.Binary(sosync="True")
    #pvpToken_crt_pem_filename = fields.Char(sosync="True")
    #pvpToken_crt_pem_path = fields.Char(sosync="True")

    #pvpToken_prvkey_pem = fields.Binary(sosync="True")
    #pvpToken_prvkey_pem_filename = fields.Char(sosync="True")
    #pvpToken_prvkey_pem_path = fields.Char(sosync="True")

    #BPKRequestURL = fields.Selection(sosync="True")
