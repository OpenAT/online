# -*- coding: utf-8 -*-
# Copyright 2018, XOE Solutions
# Copyright 2019 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2018 Rafis Bikbov <https://it-projects.info/team/bikbov>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
# pylint: disable=redefined-builtin
import logging

from openerp import http

from . import pinguin

_logger = logging.getLogger(__name__)

#################################################################
# Odoo REST API                                                 #
#  Version 1                                                    #
# --------------------------------------------------------------#
# The current api version is considered stable, although        #
# the exposed models and methods change as they are configured  #
# on the database level. Only if significant changes in the api #
# generation logic should be implemented in the future          #
# a version bump should be considered.                          #
#################################################################

API_ENDPOINT = "/api"
API_ENDPOINT_V1 = "/v1"
# API_ENDPOINT_V2 = '/v2'

# We patch the route decorator in pinguin.py
# with authentication and DB inference logic.
# We also check if the model is installed in the database.
# Furthermore we check if api version is supported.
# This keeps the code below minial and readable.


class ApiV1Controller(http.Controller):
    """ Implements the REST API V1 endpoint.
    .. methods:

        CRUD Methods:
        - `POST     .../<endpoint_model>`               -> `CreateOne`
        - `PUT      .../<endpoint_model>/<id>`          -> `UpdateOne`
        - `GET      .../<endpoint_model>`               -> `ReadMulti`
        - `GET      .../<endpoint_model>/<id>`          -> `ReadOne`
        - `DELETE   .../<endpoint_model>/<id>`          -> `UnlinkOne`

        Auxiliary Methods:
        - `PATCH    .../<endpoint_model>/<id>/<method>`               -> `Call Method on Singleton Record`
        - `PATCH    .../<endpoint_model>/<method>`                    -> `Call Method on RecordSet`
        - `GET      .../report/pdf/<report_external_id>`     -> `Get Report as PDF`
        - `GET      .../report/html/<report_external_id>`    -> `Get Report as HTML`
    """

    _api_endpoint = API_ENDPOINT + API_ENDPOINT_V1
    _api_endpoint = _api_endpoint + "/<endpoint_namespace>"
    # CreateOne # ReadMulti
    _api_endpoint_model = _api_endpoint + "/<endpoint_model>"
    # ReadOne # UpdateOne # UnlinkOne
    _api_endpoint_model_id = _api_endpoint + "/<endpoint_model>/<int:id>"
    # Call Method on Singleton Record
    _api_endpoint_model_id_method = (
        _api_endpoint + "/<endpoint_model>/<int:id>/call/<method_name>"
    )
    # Call Method on RecordSet
    _api_endpoint_model_method = _api_endpoint + "/<endpoint_model>/call/<method_name>"
    _api_endpoint_model_method_ids = _api_endpoint + "/<endpoint_model>/call/<method_name>/<ids>"
    # Get Reports
    _api_report_docids = (
        _api_endpoint
        + "/report/<any(pdf, html):converter>/<report_external_id>/<docids>"
    )

    # #################
    # # CRUD Methods ##
    # #################

    # CreateOne
    @pinguin.route(
        _api_endpoint_model, methods=["POST"], type="apijson", auth="none", csrf=False
    )
    def create_one__POST(self, endpoint_namespace, endpoint_model, **data):
        conf = pinguin.get_model_openapi_access(endpoint_namespace, endpoint_model)

        # Check if the method is allowed
        pinguin.method_is_allowed(
            "api_create", conf["method"], main=True, raise_exception=True
        )

        # By mike: Check if the fields are allowed
        pinguin.fields_are_allowed(
            "api_create", data, conf["in_fields_api_create_blacklist"],
        )

        # FIXME: What is contained in context and for what?
        # # If context is not a python dict
        # # TODO unwrap
        # if isinstance(kw.get('context'), basestring):
        #     context = get_create_context(namespace, model, kw.get('context'))
        # else:
        #     context = kw.get('context') or {}
        return pinguin.wrap__resource__create_one(
            modelname=endpoint_model,
            context=conf["context"],
            data=data,
            success_code=pinguin.CODE__created,
            out_fields=conf["out_fields_read_one"],
        )

    # ReadMulti (optional: filters, offset, limit, order, include_fields, exclude_fields):
    @pinguin.route(
        _api_endpoint_model, methods=["GET"], type="http", auth="none", csrf=False
    )
    def read_multi__GET(self, endpoint_namespace, endpoint_model, **kw):
        conf = pinguin.get_model_openapi_access(endpoint_namespace, endpoint_model)
        pinguin.method_is_allowed(
            "api_read", conf["method"], main=True, raise_exception=True
        )
        return pinguin.wrap__resource__read_all(
            modelname=endpoint_model,
            success_code=pinguin.CODE__success,
            out_fields=conf["out_fields_read_multi"],
        )

    # ReadOne (optional: include_fields, exclude_fields)
    @pinguin.route(
        _api_endpoint_model_id, methods=["GET"], type="http", auth="none", csrf=False
    )
    def read_one__GET(self, endpoint_namespace, endpoint_model, id, **kw):
        conf = pinguin.get_model_openapi_access(endpoint_namespace, endpoint_model)
        pinguin.method_is_allowed(
            "api_read", conf["method"], main=True, raise_exception=True
        )
        return pinguin.wrap__resource__read_one(
            modelname=endpoint_model,
            id=id,
            success_code=pinguin.CODE__success,
            out_fields=conf["out_fields_read_one"],
        )

    # UpdateOne
    @pinguin.route(
        _api_endpoint_model_id, methods=["PUT"], type="apijson", auth="none", csrf=False
    )
    def update_one__PUT(self, endpoint_namespace, endpoint_model, id, **data):
        conf = pinguin.get_model_openapi_access(endpoint_namespace, endpoint_model)

        pinguin.method_is_allowed(
            "api_update", conf["method"], main=True, raise_exception=True
        )

        # By mike: Check if the fields are allowed
        pinguin.fields_are_allowed(
            "api_update", data, conf["in_fields_api_update_blacklist"],
        )

        return pinguin.wrap__resource__update_one(
            modelname=endpoint_model, id=id, success_code=pinguin.CODE__ok_no_content, data=data
        )

    # UnlinkOne
    @pinguin.route(
        _api_endpoint_model_id, methods=["DELETE"], type="http", auth="none", csrf=False
    )
    def unlink_one__DELETE(self, endpoint_namespace, endpoint_model, id, **data):
        conf = pinguin.get_model_openapi_access(endpoint_namespace, endpoint_model)
        pinguin.method_is_allowed(
            "api_delete", conf["method"], main=True, raise_exception=True
        )
        return pinguin.wrap__resource__unlink_one(
            modelname=endpoint_model, id=id, success_code=pinguin.CODE__ok_no_content
        )

    # ######################
    # # Auxiliary Methods ##
    # ######################

    # Call Method on Singleton Record (optional: method parameters)
    @pinguin.route(
        _api_endpoint_model_id_method,
        methods=["PATCH"],
        type="apijson",
        auth="none",
        csrf=False,
    )
    def call_method_one__PATCH(
        self, endpoint_namespace, endpoint_model, id, method_name, **method_params
    ):
        conf = pinguin.get_model_openapi_access(endpoint_namespace, endpoint_model)
        pinguin.method_is_allowed(method_name, conf["method"])
        return pinguin.wrap__resource__call_method(
            modelname=endpoint_model,
            ids=[id],
            method=method_name,
            method_params=method_params,
            success_code=pinguin.CODE__success,
        )

    # Call Method on RecordSet (optional: method parameters)
    @pinguin.route(
        [_api_endpoint_model_method, _api_endpoint_model_method_ids],
        methods=["PATCH"],
        type="apijson",
        auth="none",
        csrf=False,
    )
    def call_method_multi__PATCH(
        self, endpoint_namespace, endpoint_model, method_name, ids=None, **method_params
    ):
        conf = pinguin.get_model_openapi_access(endpoint_namespace, endpoint_model)
        pinguin.method_is_allowed(method_name, conf["method"])
        ids = ids and ids.split(",") or []
        ids = [int(i) for i in ids]
        return pinguin.wrap__resource__call_method(
            modelname=endpoint_model,
            ids=ids,
            method=method_name,
            method_params=method_params,
            success_code=pinguin.CODE__success,
        )

    # Get Report
    @pinguin.route(
        _api_report_docids, methods=["GET"], type="http", auth="none", csrf=False
    )
    def report__GET(self, converter, endpoint_namespace, report_external_id, docids):
        return pinguin.wrap__resource__get_report(
            namespace=endpoint_namespace,
            report_external_id=report_external_id,
            docids=docids,
            converter=converter,
            success_code=pinguin.CODE__success,
        )
