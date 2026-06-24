# -*- coding: utf-8 -*-
from odoo.tools import sql


def migrate(cr, version):
    for table, column in (
        ('pos_session', 'two_book_vat_move_id'),
        ('pos_config', 'two_book_vat_clearing_account_id'),
    ):
        if not sql.column_exists(cr, table, column):
            sql.create_column(cr, table, column, 'int4')
