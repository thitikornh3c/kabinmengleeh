from odoo import models, fields, _
from odoo.exceptions import UserError
from collections import defaultdict

class PosOrder(models.Model):
    _inherit = 'pos.order'

    invoice_id = fields.Many2one('account.move', string="Invoice")
    
    def _merge_and_create_invoice(self):
        if not self:
            raise UserError(_("No POS Orders selected"))

        partner = self[0].partner_id
        if any(order.partner_id != partner for order in self):
            raise UserError(_("All selected POS Orders must belong to the same customer."))

        merged_lines = defaultdict(lambda: {'quantity': 0.0, 'price_unit': 0.0, 'taxes': self.env['account.tax']})

        for order in self:
            for line in order.lines:
                key = (line.product_id.id, line.price_unit)
                merged_lines[key]['quantity'] += line.qty
                merged_lines[key]['price_unit'] = line.price_unit
                merged_lines[key]['taxes'] += line.tax_ids

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_origin': ', '.join(self.mapped('name')),
            'invoice_line_ids': [],
        }

        for (product_id, price_unit), data in merged_lines.items():
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': product_id,
                'quantity': data['quantity'],
                'price_unit': price_unit,
                'tax_ids': [(6, 0, data['taxes'].ids)],
                'name': self.env['product.product'].browse(product_id).name,
            }))

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()

        self.write({'account_move': invoice.id})
        return invoice
