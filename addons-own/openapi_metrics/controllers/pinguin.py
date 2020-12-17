# -*- coding: utf-8 -*-

import logging
import openerp

from openerp.addons.openapi.controllers import pinguin
from openerp.http import request


_logger = logging.getLogger(__name__)
_super_create_log_record = pinguin.create_log_record


def create_log_and_metrics_record(**kwargs):
    test_mode = request.registry.test_cr

    if not test_mode:
        with openerp.registry(request.session.db).cursor() as cr:
            # Custom new cursor, so metrics can be written even if
            # parent cursor has errors.
            _create_metric_record(cr=cr, uid=request.session.uid)

    return _super_create_log_record(**kwargs)


def _create_metric_record(cr, uid):
    uid = int(uid)

    # Use raw SQL in order to utilize postgres UPSERT,
    # for fastest possible insert/update.
    query = """
        INSERT INTO openapi_http_metric AS m (day, request_count, create_uid, create_date)
        VALUES (current_date, 1, {0}, now() at time zone 'utc')
        ON CONFLICT (day) DO UPDATE
        SET request_count = m.request_count + 1,
        write_date = now() at time zone 'utc',
        write_uid = {0};
        """.format(uid)
    cr.execute(query)


# Monkey patch log method with metrics method
pinguin.create_log_record = create_log_and_metrics_record
