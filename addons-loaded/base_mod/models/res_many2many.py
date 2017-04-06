

from openerp import fields, SUPERUSER_ID
from openerp import models, osv
#from openerp.osv.orm import BaseModel, Model, MAGIC_COLUMNS, except_orm


# class ir_model_fields(osv.osv):
#     _inherit = 'ir.model.fields'
#
#     _columns = {
#         'db_column': fields.char('Column Name in Rel Table'),
#     }

    # TODO: Get the Column Name of the rel_table of many2many fields for sosync
    # See: odoo/openerp/osv/fields.py >> def _sql_names(self, source_model):

