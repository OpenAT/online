from openerp.models import BaseModel


class BaseModelDropConstraintFix(BaseModel):

    # Ugly hack to escape (add "" to) the constraint_name in case of uppercase letters or alike in the name!
    def _drop_constraint(self, cr, source_table, constraint_name):
        cr.execute('ALTER TABLE %s DROP CONSTRAINT \"%s\"' % (source_table, constraint_name))
