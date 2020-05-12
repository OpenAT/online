# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


class ResPartnerFSOMergeConZmr(models.Model):
    _name = "res.partner"

    # ---------
    # FSO MERGE
    # ---------
    @api.model
    def _fso_merge_pre(self, rec_to_remove=None, rec_to_keep=None):
        res = super(ResPartnerFSOMergeConZmr, self)._fso_merge_pre(rec_to_remove=rec_to_remove, rec_to_keep=rec_to_keep)

        # Delete BPK Requests
        if rec_to_remove.bpk_request_ids:
            logger.info("FSO MERGE FOR res.partner: _fso_merge_pre() remove bpk records for the partner-to-remove "
                        "before the merge with the ids: %s" % rec_to_remove.bpk_request_ids.ids)
            rec_to_remove.bpk_request_ids.unlink()

        return res
