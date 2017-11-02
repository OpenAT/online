# -*- coding: utf-8 -*-
import os
from os.path import join as pj
from openerp import api, models, fields
from openerp.exceptions import ValidationError, Warning
from openerp.tools.translate import _
from openerp.addons.fso_base.tools.soap import soap_request, GenericTimeoutError
from openerp.addons.fso_base.tools.name import clean_name
from lxml import etree
import time
import datetime
from datetime import timedelta
from dateutil import tz
import logging
from requests import Timeout
import pprint
pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)


class ResPartnerFASendReport(models.Model):
    _inherit = 'res.partner'

    # FIELDS
    # Spendenmeldungen
    fa_donation_report_ids = fields.One2many(comodel_name="res.partner.fa_donation_report", inverse_name="partner_id",
                                             string="Donation Reports")
    fa_donation_report_error = fields.Text(string="Donation Report Submission Error")

