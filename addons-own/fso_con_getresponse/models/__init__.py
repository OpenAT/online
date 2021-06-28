# -*- coding: utf-8 -*-

# ATTENTION: Do not use from . import ... in __init__.py files or it may mess up odoo 8

import queue_job
import res_partner

import helper_connector
import helper_related_action
import helper_consumer

import backend
import getresponse_backend

import unit_binder
import unit_adapter
import unit_import
import unit_export
import unit_export_delete

# Campaigns
import getresponse_frst_zgruppedetail
import getresponse_frst_zgruppedetail_import
import getresponse_frst_zgruppedetail_export
# TODO: import getresponse_frst_zgruppedetail_consumer

# Custom Fields
import gr_custom_field
import getresponse_gr_custom_field
import getresponse_gr_custom_field_export
import getresponse_gr_custom_field_import
import getresponse_gr_custom_field_consumer

# Tags
import gr_tag
import getresponse_gr_tag
import getresponse_gr_tag_export
import getresponse_gr_tag_import
import getresponse_gr_tag_consumer

# Contacts (Subscriptions)
import frst_personemailgruppe
import getresponse_frst_personemailgruppe
import getresponse_frst_personemailgruppe_export
import getresponse_frst_personemailgruppe_import
import getresponse_frst_personemailgruppe_consumer
