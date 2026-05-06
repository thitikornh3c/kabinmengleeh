# -*- coding: utf-8 -*-
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # --- Two Book Settings ---
    enable_two_book = fields.Boolean(
        string='เปิดใช้งาน Two Book (VAT/Non-VAT)',
        default=False,
        help='เปิดใช้งานระบบแยกการขาย VAT และ Non-VAT'
    )

    # VAT Side
    two_book_vat_journal_id = fields.Many2one(
        'account.journal',
        string='Journal สำหรับใบกำกับภาษี (VAT)',
        domain=[('type', 'in', ['sale'])],
        help='Journal ที่ใช้บันทึกรายการขายแบบ VAT'
    )
    two_book_vat_fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        string='Fiscal Position (VAT 7%)',
        help='Fiscal Position สำหรับการขายที่มี VAT 7%'
    )

    # Non-VAT Side
    two_book_non_vat_journal_id = fields.Many2one(
        'account.journal',
        string='Journal สำหรับบิลเงินสด (Non-VAT)',
        domain=[('type', 'in', ['sale', 'general'])],
        help='Journal ที่ใช้บันทึกรายการขายแบบ Non-VAT'
    )
    two_book_non_vat_fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        string='Fiscal Position (Non-VAT / Exempt)',
        help='Fiscal Position สำหรับการขายที่ไม่มี VAT (Exempt)'
    )

    # Default behavior
    two_book_default_vat = fields.Boolean(
        string='ค่าเริ่มต้น: ออกใบกำกับภาษี',
        default=False,
        help='ถ้าเปิด = ทุก Order จะเริ่มต้นเป็น VAT Order'
    )
