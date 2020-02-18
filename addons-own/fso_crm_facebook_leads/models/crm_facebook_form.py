# -*- coding: utf-8 -*-

from openerp import api, models, fields

import logging
logger = logging.getLogger(__name__)


class FSOCrmFacebookForm(models.Model):
    _inherit = 'crm.facebook.form'

    force_create_partner = fields.Boolean(string="Force Create Partner",
                                          default=True,
                                          help="If enabled leads will be created in state 'opportunity' and therefore "
                                               "create a partner and link to the lead! This is useful for "
                                               "Fundraising Studio where a partner is needed to create the lead as an"
                                               "'Aktion'")

    # TODO: Fields to link PersonEmailGruppe and PersonGruppe
    #       which will be set on the lead and then on the res.partner or PersonEmail
