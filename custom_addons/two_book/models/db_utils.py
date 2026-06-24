# -*- coding: utf-8 -*-
from odoo.tools import sql


def ensure_m2o_column(cr, table, column):
    if not sql.column_exists(cr, table, column):
        sql.create_column(cr, table, column, 'int4')
