# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_vat_order = fields.Boolean(
        string='ออกใบกำกับภาษี (VAT)',
        default=False,
        help='True = ออกใบกำกับภาษีเต็มรูปแบบ (7%), False = บิลเงินสด / ไม่ออกใบกำกับ'
    )
    two_book_type = fields.Selection([
        ('vat', 'ใบกำกับภาษี (VAT 7%)'),
        ('non_vat', 'บิลเงินสด (Non-VAT)'),
    ], string='ประเภทเอกสาร', compute='_compute_two_book_type', store=True)

    tax_invoice_number = fields.Char(
        string='เลขที่ใบกำกับภาษี',
        readonly=True,
        copy=False,
    )

    @api.depends('is_vat_order')
    def _compute_two_book_type(self):
        for order in self:
            order.two_book_type = 'vat' if order.is_vat_order else 'non_vat'

    def _get_pos_anglo_saxon_price_unit(self, product, partner_id, quantity):
        return super()._get_pos_anglo_saxon_price_unit(product, partner_id, quantity)

    def _prepare_invoice_vals(self):
        """Override เพื่อกำหนด Journal และ Fiscal Position ตามประเภทการขาย"""
        vals = super()._prepare_invoice_vals()
        config = self.session_id.config_id

        if self.is_vat_order:
            # ใช้ VAT Journal และ Fiscal Position ปกติ
            if config.two_book_vat_journal_id:
                vals['journal_id'] = config.two_book_vat_journal_id.id
            if config.two_book_vat_fiscal_position_id:
                vals['fiscal_position_id'] = config.two_book_vat_fiscal_position_id.id
        else:
            # ใช้ Non-VAT Journal และ Fiscal Position แบบ Exempt
            if config.two_book_non_vat_journal_id:
                vals['journal_id'] = config.two_book_non_vat_journal_id.id
            if config.two_book_non_vat_fiscal_position_id:
                vals['fiscal_position_id'] = config.two_book_non_vat_fiscal_position_id.id

        return vals

    def action_pos_order_invoice(self):
        """Override เพื่อกำหนดเลขที่ใบกำกับภาษีเฉพาะ VAT order"""
        res = super().action_pos_order_invoice()
        for order in self:
            if order.is_vat_order and order.account_move:
                order.tax_invoice_number = order.account_move.name
        return res

    @api.model
    def _order_fields(self, ui_order):
        """รับค่า is_vat_order จาก POS UI"""
        fields_return = super()._order_fields(ui_order)
        fields_return['is_vat_order'] = ui_order.get('is_vat_order', False)
        return fields_return

    def _export_for_ui(self, order):
        """ส่งค่า is_vat_order กลับไปยัง POS UI"""
        result = super()._export_for_ui(order)
        result['is_vat_order'] = order.is_vat_order
        return result


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def _get_tax_ids_after_fiscal_position(self):
        """ปรับ Tax ตาม Fiscal Position ของ Order (VAT vs Non-VAT)"""
        order = self.order_id
        config = order.session_id.config_id

        if not order.is_vat_order and config.two_book_non_vat_fiscal_position_id:
            # Non-VAT: map tax ผ่าน Non-VAT Fiscal Position
            fiscal_position = config.two_book_non_vat_fiscal_position_id
            return fiscal_position.map_tax(self.tax_ids)

        return super()._get_tax_ids_after_fiscal_position()
