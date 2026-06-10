# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    # สรุปยอดแยก VAT / Non-VAT สำหรับ End of Day
    two_book_vat_total = fields.Monetary(
        string='ยอดขาย VAT รวม',
        compute='_compute_two_book_totals',
        currency_field='currency_id',
    )
    two_book_non_vat_total = fields.Monetary(
        string='ยอดขาย Non-VAT รวม',
        compute='_compute_two_book_totals',
        currency_field='currency_id',
    )
    two_book_vat_tax_total = fields.Monetary(
        string='ภาษีขาย (Output VAT) รวม',
        compute='_compute_two_book_totals',
        currency_field='currency_id',
    )

    @api.depends('order_ids', 'order_ids.amount_total', 'order_ids.is_vat_order')
    def _compute_two_book_totals(self):
        for session in self:
            vat_orders = session.order_ids.filtered(
                lambda o: o.is_vat_order and o.state not in ['cancel']
            )
            non_vat_orders = session.order_ids.filtered(
                lambda o: not o.is_vat_order and o.state not in ['cancel']
            )

            session.two_book_vat_total = sum(vat_orders.mapped('amount_total'))
            session.two_book_non_vat_total = sum(non_vat_orders.mapped('amount_total'))

            # คำนวณ Output VAT จาก VAT orders (amount_tax)
            session.two_book_vat_tax_total = sum(vat_orders.mapped('amount_tax'))
