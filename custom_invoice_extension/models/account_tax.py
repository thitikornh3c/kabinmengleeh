from odoo import models, api
import math
import logging
_logger = logging.getLogger(__name__)

class AccountTax(models.Model):
    _inherit = 'account.tax'

    # @api.model
    # def _prepare_tax_lines_dict(self, tax_lines_data):
    #     """Override tax line preparation to apply custom rounding logic"""
    #     res = super()._prepare_tax_lines_dict(tax_lines_data)
    #     _logger.info(f"Custom Rounding: Invoice in context: {res}")

    #     if self.name == 'INV20250228001':  # Or use a custom field here
    #         for line in res:
    #             amount = line.get('amount', 0.0)
    #             currency = self.currency_id
    #             precision = currency.decimal_places if currency else 2
    #             factor = 10 ** precision
    #             rounded = math.floor(amount * factor) / factor
    #             _logger.info(f"[Rounding Override] {self.name} - VAT {amount} → {rounded}")
    #             line['amount'] = rounded

    #     return res
    @api.model
    def _round_tax_amount(self, amount, currency=None):
        # Check for invoice name condition in context
        invoice = self.env.context.get('invoice')
        _logger.info(f"ReComputed invoice: {invoice}")
        if invoice and invoice.name == 'INV20250228001':
            # Custom rounding: round down
            precision = currency.decimal_places if currency else 2
            factor = 10 ** precision
            return math.floor(amount * factor) / factor
        else:
            # Default Odoo rounding
            return currency.round(amount) if currency else round(amount, 2)

    # @api.model
    # def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None, is_refund=False):
    #         """Override the tax computation to round down for a specific invoice"""
    #         tax_amount = super()._compute_amount(
    #             base_amount, price_unit, quantity, product, partner, is_refund
    #         )

    #         move_id = self.env.context.get('move_id')
    #         _logger.info(f"Custom Rounding: Invoice in context: {move_id}")

    #         move = self.env['account.move'].browse(move_id) if move_id else None
    #         _logger.info(f"Custom Rounding: Invoice in context: {self}")

    #         if move and move.name == 'INV20250228001':
    #             currency = move.currency_id
    #             precision = currency.decimal_places if currency else 2
    #             factor = 10 ** precision
    #             rounded = math.floor(tax_amount * factor) / factor
    #             _logger.info(f"Tax rounded down for {move.name}: {tax_amount} → {rounded}")
    #             return rounded

    #         return tax_amount