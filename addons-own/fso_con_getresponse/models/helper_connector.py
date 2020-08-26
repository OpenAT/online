# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.checkpoint import checkpoint

import logging
_logger = logging.getLogger(__name__)


def get_environment(session, model_name, backend_id):
    """ Create an environment to work with. """
    backend_record = session.env['getresponse.backend'].browse(backend_id)

    # Get a connector environment for the given model
    con_env = ConnectorEnvironment(backend_record, session, model_name)

    # Change the language based on the backend setting and return the env
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'de_de'
    if lang_code == session.context.get('lang'):
        return con_env
    else:
        with con_env.session.change_context(lang=lang_code):
            return con_env


def add_checkpoint(session, model_name, record_id, backend_id):
    """ Add a row in the model ``connector.checkpoint`` for a record,
    meaning it has to be reviewed by a user.
    :param session: current session
    :type session: :class:`openerp.addons.connector.session.ConnectorSession`
    :param model_name: name of the model of the record to be reviewed
    :type model_name: str
    :param record_id: ID of the record to be reviewed
    :type record_id: int
    :param backend_id: ID of the GetResponse Backend
    :type backend_id: int
    """
    return checkpoint.add_checkpoint(session, model_name, record_id, 'getresponse.backend', backend_id)


def skipp_export_by_context(context, skipp_only_bind_model=None, skipp_only_bind_record_id=None):
    if skipp_only_bind_record_id:
        assert skipp_only_bind_model, "skipp_only_bind_model is given but skipp_only_bind_record_id is missing!"

    context = context if context else {}

    if 'connector_no_export' not in context:
        connector_no_export = 'not_in_context'
    else:
        connector_no_export = context['connector_no_export']

    # Not found in context
    if connector_no_export == 'not_in_context':
        skipp_export = False

    # Skipp export for all models and all records
    elif connector_no_export is True:
        if skipp_only_bind_model or skipp_only_bind_record_id:
            _logger.warning("connector_no_export is True but skipp_only_bind_model '%s' or skipp_only_bind_record_id"
                            " '%s' are set! " % skipp_only_bind_model, skipp_only_bind_record_id)
        skipp_export = True

    # Skipp exports only if the model and the record id are in 'connector_no_export'
    elif skipp_only_bind_record_id:
        skipp_ids = connector_no_export.get(skipp_only_bind_model, [])
        skipp_ids = skipp_ids if isinstance(skipp_ids, list) else [skipp_ids]
        skipp_export = True if skipp_only_bind_record_id in skipp_ids else False

    # Skipp exports only if the model is in 'connector_no_export'
    elif skipp_only_bind_model:
        skipp_export = True if skipp_only_bind_model in connector_no_export else False

    # Unexpected value type for 'connector_no_export'
    else:
        raise TypeError("'connector_no_export' (%s) must be of type 'True' or 'dict'!" % connector_no_export)

    if skipp_export:
        _logger.info("Skipp export of binding record ('%s', '%s') because of 'connector_no_export' (%s) in context!"
                     "" % (skipp_only_bind_model, skipp_only_bind_record_id, connector_no_export))

    return skipp_export
