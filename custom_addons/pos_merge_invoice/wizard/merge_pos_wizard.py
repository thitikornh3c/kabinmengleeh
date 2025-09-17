from odoo import models, fields, api
from odoo.exceptions import UserError

class MergePOSOrdersWizard(models.TransientModel):
    _name = 'merge.pos.orders.wizard'
    _description = 'Merge POS Orders Wizard'

    pos_order_ids = fields.Many2many('pos.order', string="POS Orders")

    def action_merge_and_invoice(self):
        AccountMove = self.env['account.move']

        generic_partner = self.env['res.partner'].search([('name', '=', 'Walk-in Customer')], limit=1)
        if not generic_partner:
            raise UserError("Please create a partner named 'Walk-in Customer' before merging POS orders.")

        merged_lines = {}

        for order in self.pos_order_ids:
            for line in order.lines:
                product_id = line.product_id.id
                if product_id in merged_lines:
                    merged_lines[product_id]['quantity'] += line.qty
                else:
                    merged_lines[product_id] = {
                        'product_id': product_id,
                        'quantity': line.qty,
                        'price_unit': line.price_unit,
                        'name': line.product_id.name,
                    }

        invoice_lines = [(0, 0, {
            'product_id': vals['product_id'],
            'quantity': vals['quantity'],
            'price_unit': vals['price_unit'],
            'name': vals['name'],
        }) for vals in merged_lines.values()]

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': generic_partner.id,
            'invoice_line_ids': invoice_lines,
            'invoice_origin': ', '.join(self.pos_order_ids.mapped('name')),
        }

        invoice = AccountMove.create(invoice_vals)

        # Link invoice to POS orders via the new field
        # self.pos_order_ids.write({'invoice_id': invoice.id})
        self.pos_order_ids.write({
            'invoice_id': invoice.id,
            'state': 'invoiced' # Set the state to 'invoiced'
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
