# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.checkpoint import checkpoint


def get_environment(session, model_name, backend_id):
    """ Create an environment to work with. """
    backend_record = session.env['getresponse.backend'].browse(backend_id)
    con_env = ConnectorEnvironment(backend_record, session, model_name)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
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
