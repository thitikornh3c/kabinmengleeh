# -*- coding: utf-8 -*-
from odoo import api, models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_two_book = fields.Boolean(
        string='เปิดใช้งาน Two Book (VAT/Non-VAT)',
        default=False,
        help='เปิดใช้งานระบบแยกการขาย VAT และ Non-VAT',
    )

    two_book_vat_journal_id = fields.Many2one(
        'account.journal',
        string='Journal สำหรับใบกำกับภาษี (VAT)',
        domain=[('type', 'in', ['sale'])],
        help='Journal ที่ใช้บันทึกรายการขายแบบ VAT',
    )
    two_book_vat_fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        string='Fiscal Position (VAT 7%)',
        help='Fiscal Position สำหรับการขายที่มี VAT 7%',
    )

    two_book_non_vat_journal_id = fields.Many2one(
        'account.journal',
        string='Journal สำหรับบิลเงินสด (Non-VAT)',
        domain=[('type', 'in', ['sale', 'general'])],
        help='Journal ที่ใช้บันทึกรายการขายแบบ Non-VAT',
    )
    two_book_non_vat_fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        string='Fiscal Position (Non-VAT / Exempt)',
        help='Fiscal Position สำหรับการขายที่ไม่มี VAT (Exempt)',
    )

    two_book_tax_location_id = fields.Many2one(
        'stock.location',
        string='คลังสต็อกภาษี (WH/VAT)',
        domain=[('usage', '=', 'internal')],
        help='ตัดสต็อกเล่มภาษีเฉพาะรายการขาย VAT',
    )
    two_book_vat_out_location_id = fields.Many2one(
        'stock.location',
        string='Virtual/VAT_Out',
        domain=[('usage', 'in', ['inventory', 'production'])],
        help='ปลายทางเมื่อตัดสต็อกเล่มภาษี',
    )
    two_book_tax_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type (Tax Stock)',
        domain=[('code', '=', 'internal')],
        help='ใช้สร้าง internal transfer สำหรับเล่มภาษี',
    )

    two_book_default_vat = fields.Boolean(
        string='ค่าเริ่มต้น: ออกใบกำกับภาษี',
        default=False,
        help='ถ้าเปิด = ทุก Order จะเริ่มต้นเป็น VAT Order',
    )
    two_book_vat_clearing_account_id = fields.Many2one(
        'account.account',
        string='บัญชีพัก VAT (Clearing)',
        domain=[('account_type', 'in', ['liability_current', 'liability_non_current'])],
        help='บัญชีพักรายได้ VAT สำหรับ order ที่รอ merge/invoice ตอนปิด session',
    )

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = list(super()._load_pos_data_fields(config))
        extra = [
            'enable_two_book',
            'two_book_default_vat',
            'two_book_vat_fiscal_position_id',
            'two_book_non_vat_fiscal_position_id',
        ]
        if fields_list:
            return fields_list + [f for f in extra if f not in fields_list]
        return fields_list

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        tax_loc = self.env.ref('two_book.stock_location_wh_vat', raise_if_not_found=False)
        vat_out = self.env.ref('two_book.stock_location_vat_out', raise_if_not_found=False)
        fp_vat = self.env.ref('two_book.fiscal_position_vat_th', raise_if_not_found=False)
        fp_non = self.env.ref('two_book.fiscal_position_non_vat_th', raise_if_not_found=False)
        journal_non = self.env.ref('two_book.journal_non_vat_sales', raise_if_not_found=False)
        clearing = self.env.ref('two_book.account_vat_clearing', raise_if_not_found=False)
        sale_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if tax_loc and 'two_book_tax_location_id' in fields_list:
            res.setdefault('two_book_tax_location_id', tax_loc.id)
        if vat_out and 'two_book_vat_out_location_id' in fields_list:
            res.setdefault('two_book_vat_out_location_id', vat_out.id)
        if fp_vat and 'two_book_vat_fiscal_position_id' in fields_list:
            res.setdefault('two_book_vat_fiscal_position_id', fp_vat.id)
        if fp_non and 'two_book_non_vat_fiscal_position_id' in fields_list:
            res.setdefault('two_book_non_vat_fiscal_position_id', fp_non.id)
        if journal_non and 'two_book_non_vat_journal_id' in fields_list:
            res.setdefault('two_book_non_vat_journal_id', journal_non.id)
        if sale_journal and 'two_book_vat_journal_id' in fields_list:
            res.setdefault('two_book_vat_journal_id', sale_journal.id)
        if clearing and 'two_book_vat_clearing_account_id' in fields_list:
            res.setdefault('two_book_vat_clearing_account_id', clearing.id)
        return res
