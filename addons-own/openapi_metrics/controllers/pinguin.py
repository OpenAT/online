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
            _create_metric_record(
                cr=cr,
                namespace_id=kwargs["namespace_id"],
                namespace_name=kwargs["namespace"],
                uid=request.session.uid,
                model=kwargs["model"])

    return _super_create_log_record(**kwargs)


def _create_metric_record(cr, namespace_id, namespace_name, uid, model):
    # Use raw SQL in order to utilize postgres UPSERT,
    # for fastest possible insert/update.
    query = """
        INSERT INTO openapi_http_metric AS m (
            namespace_id,
            namespace_name,
            day,
            model,
            request_count,
            create_uid,
            create_date
            )
        VALUES (
            %(namespace_id)s,           -- namespace_id
            %(namespace_name)s,         -- namespace_name
            current_date,               -- day
            %(model)s,                  -- model
            1,                          -- request_count
            %(uid)s,                    -- create_uid
            now() at time zone 'utc'    -- create_date
            )
        ON CONFLICT (namespace_id, day, model) DO UPDATE SET
            request_count = m.request_count + 1,
            write_date = now() at time zone 'utc',
            write_uid = %(uid)s;
        """
    cr.execute(
        query,
        {
            "namespace_id": namespace_id,
            "namespace_name": namespace_name,
            "uid": uid,
            "model": model
        })


# Monkey patch log method with metrics method
pinguin.create_log_record = create_log_and_metrics_record
