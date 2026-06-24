# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_tax_stock_move = fields.Boolean(
        string='Tax Stock Move',
        default=False,
        copy=False,
        help='Move from Tax Warehouse (WH/VAT) for VAT POS sales',
    )
    two_book_pos_order_id = fields.Many2one(
        'pos.order',
        string='Two Book POS Order',
        copy=False,
        index=True,
    )
