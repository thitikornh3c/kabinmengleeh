# -*- coding: utf-8 -*-
from odoo import fields, models


class TwoBookStockGap(models.Model):
    _name = 'two.book.stock.gap'
    _description = 'Two Book Stock Gap (Non-VAT sales)'
    _order = 'create_date desc, id desc'

    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    session_id = fields.Many2one(
        'pos.session',
        string='POS Session',
        related='pos_order_id.session_id',
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        index=True,
    )
    quantity = fields.Float(string='Gap Qty', digits='Product Unit', required=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('reconciled', 'Reconciled'),
    ], string='Status', default='open', required=True, index=True)
    two_book_type = fields.Selection(
        related='pos_order_id.two_book_type',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        related='pos_order_id.company_id',
        store=True,
        readonly=True,
    )
