# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class MergePOSOrdersWizard(models.TransientModel):
    _inherit = 'merge.pos.orders.wizard'

    def _two_book_validate_merge_orders(self, orders):
        two_book_orders = orders.filtered(lambda o: o.config_id.enable_two_book)
        if not two_book_orders:
            return
        non_vat = two_book_orders.filtered(lambda o: not o.is_vat_order)
        if non_vat:
            raise UserError(_(
                "Two Book: Cannot merge Non-VAT orders (%(orders)s). "
                "Select VAT orders only.",
                orders=', '.join(non_vat.mapped('name')),
            ))

    def action_merge_and_invoice(self):
        orders = self.pos_order_ids
        if not orders:
            raise UserError(_("Please select at least one POS order."))

        self._two_book_validate_merge_orders(orders)

        if any(order.account_move for order in orders):
            raise UserError(_("One or more selected orders are already invoiced."))

        partners = orders.mapped('partner_id')
        if len(partners) > 1:
            raise UserError(_("All selected POS orders must belong to the same customer."))

        partner = partners[0]
        if not partner:
            partner = self.env['res.partner'].search([('name', '=', 'Walk-in Customer')], limit=1)
            if not partner:
                raise UserError(_("Please set a customer on the orders or create 'Walk-in Customer'."))

        merged_lines = {}
        for order in orders:
            for line in order.lines:
                key = (line.product_id.id, line.price_unit)
                if key in merged_lines:
                    merged_lines[key]['quantity'] += line.qty
                else:
                    merged_lines[key] = {
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'price_unit': line.price_unit,
                        'name': line.full_product_name or line.product_id.display_name,
                        'tax_ids': line.tax_ids,
                    }

        invoice_lines = [
            (0, 0, {
                'product_id': vals['product_id'],
                'quantity': vals['quantity'],
                'price_unit': vals['price_unit'],
                'name': vals['name'],
                'tax_ids': [(6, 0, vals['tax_ids'].ids)],
            })
            for vals in merged_lines.values()
        ]

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': invoice_lines,
            'invoice_origin': ', '.join(orders.mapped('name')),
        }
        invoice_vals.update(orders[0].get_two_book_merge_invoice_vals())

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()

        orders.write({
            'invoice_id': invoice.id,
            'account_move': invoice.id,
            'state': 'invoiced',
            'tax_invoice_number': invoice.name,
        })

        orders.filtered(
            lambda o: o.config_id.enable_two_book and o.is_vat_order
        )._two_book_release_vat_clearing(invoice)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
