# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class TwoBookStockGapReconcileWizard(models.TransientModel):
    _name = 'two.book.stock.gap.reconcile.wizard'
    _description = 'Reconcile Two Book Stock Gap'

    gap_ids = fields.Many2many('two.book.stock.gap', string='Stock Gaps', required=True)
    adjustment_reason = fields.Selection([
        ('usage', 'เบิกใช้ / ใช้หน้างาน'),
        ('damaged', 'เสียหาย / ชำรุด'),
        ('lost', 'สูญหาย'),
        ('disposal', 'ตัดทิ้ง / ทิ้ง'),
        ('sample', 'ตัวอย่าง / สาธิต'),
    ], string='เหตุผล', required=True, default='usage')
    note = fields.Char(string='หมายเหตุ')

    def action_reconcile(self):
        gaps = self.gap_ids.filtered(lambda g: g.state == 'open')
        if not gaps:
            raise UserError(_('ไม่มี Stock Gap ที่สถานะ Open'))

        config = gaps[0].pos_order_id.config_id
        tax_location = config.two_book_tax_location_id
        vat_out = config.two_book_vat_out_location_id
        if not tax_location or not vat_out:
            raise UserError(_('กรุณาตั้งค่า WH/VAT และ Virtual/VAT_Out ใน POS Config'))

        picking_type = config.two_book_tax_picking_type_id or self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', config.warehouse_id.id),
        ], limit=1)
        if not picking_type:
            raise UserError(_('ไม่พบ Internal Operation Type สำหรับตัดสต็อกภาษี'))

        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': tax_location.id,
            'location_dest_id': vat_out.id,
            'origin': _('Two Book Gap Reconcile'),
        })

        for gap in gaps:
            self.env['stock.move'].sudo().create({
                'name': _('Gap reconcile: %s', gap.product_id.display_name),
                'product_id': gap.product_id.id,
                'product_uom_qty': gap.quantity,
                'product_uom': gap.product_id.uom_id.id,
                'location_id': tax_location.id,
                'location_dest_id': vat_out.id,
                'picking_id': picking.id,
                'is_tax_stock_move': True,
            })

        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

        gaps.write({'state': 'reconciled'})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tax Stock Adjustment'),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }
