# -*- coding: utf-8 -*-
import functools

from openerp.addons.connector import related_action
from .unit_binder import GetResponseModelBinder

unwrap_binding = functools.partial(related_action.unwrap_binding, binder_class=GetResponseModelBinder)
