from openerp.models import BaseModel


# Monkey patching  _drop_constraint to escape the constraint name (wrap it in "")!
def _drop_constraint(self, cr, source_table, constraint_name):
    cr.execute('ALTER TABLE %s DROP CONSTRAINT \"%s\"' % (source_table, constraint_name))


BaseModel._drop_constraint = _drop_constraint
